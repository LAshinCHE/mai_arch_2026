#include "create_delivery_handler.hpp"

#include <userver/components/component_context.hpp>
#include <userver/formats/json/serialize.hpp>
#include <userver/formats/json/value_builder.hpp>
#include <userver/server/handlers/exceptions.hpp>
#include <userver/server/http/http_status.hpp>
#include <userver/storages/postgres/component.hpp>
#include <userver/storages/postgres/exceptions.hpp>

namespace delivery {

CreateDeliveryHandler::CreateDeliveryHandler(
    const userver::components::ComponentConfig& config,
    const userver::components::ComponentContext& context)
    : HttpHandlerBase(config, context),
      auth_(context.FindComponent<AuthComponent>()),
      pg_(context.FindComponent<userver::components::Postgres>("postgres-db-1").GetCluster()) {}

std::string CreateDeliveryHandler::HandleRequestThrow(
    const userver::server::http::HttpRequest& request,
    userver::server::request::RequestContext&) const {

    const auto token = AuthComponent::ExtractToken(request.GetHeader("Authorization"));
    auth_.ValidateToken(token);

    const auto body = userver::formats::json::FromString(request.RequestBody());
    const auto sender_id = body["sender_id"].As<std::string>("");
    const auto recipient_id = body["recipient_id"].As<std::string>("");
    const auto package_id = body["package_id"].As<std::string>("");
    const auto address = body["address"].As<std::string>("");

    if (sender_id.empty() || recipient_id.empty() || package_id.empty() || address.empty()) {
        throw userver::server::handlers::ClientError{};
    }

    std::string delivery_id;
    try {
        const auto result = pg_->Execute(
            userver::storages::postgres::ClusterHostType::kMaster,
            "INSERT INTO delivery.deliveries(sender_id, recipient_id, package_id, address) "
            "VALUES($1::uuid, $2::uuid, $3::uuid, $4) RETURNING id::text",
            sender_id, recipient_id, package_id, address);
        delivery_id = result[0][0].As<std::string>();
    } catch (const userver::storages::postgres::ForeignKeyViolation&) {
        throw userver::server::handlers::ClientError{};
    }

    request.GetHttpResponse().SetStatus(userver::server::http::HttpStatus::kCreated);

    userver::formats::json::ValueBuilder response;
    response["id"] = delivery_id;
    return userver::formats::json::ToString(response.ExtractValue());
}

}  // namespace delivery
