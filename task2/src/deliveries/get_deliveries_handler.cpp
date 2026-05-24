#include "get_deliveries_handler.hpp"

#include <userver/components/component_context.hpp>
#include <userver/formats/json/serialize.hpp>
#include <userver/formats/json/value_builder.hpp>
#include <userver/server/handlers/exceptions.hpp>
#include <userver/storages/postgres/component.hpp>

namespace delivery {

GetDeliveriesHandler::GetDeliveriesHandler(
    const userver::components::ComponentConfig& config,
    const userver::components::ComponentContext& context)
    : HttpHandlerBase(config, context),
      auth_(context.FindComponent<AuthComponent>()),
      pg_(context.FindComponent<userver::components::Postgres>("postgres-db-1").GetCluster()) {}

namespace {

const std::string kDeliveryQuery =
    "SELECT id::text, sender_id::text, recipient_id::text, "
    "       package_id::text, status, address, created_at::text "
    "FROM delivery.deliveries WHERE ";

std::string BuildDeliveriesJson(const userver::storages::postgres::ResultSet& result) {
    userver::formats::json::ValueBuilder arr(userver::formats::common::Type::kArray);
    for (const auto& row : result) {
        userver::formats::json::ValueBuilder d;
        d["id"] = row[0].As<std::string>();
        d["sender_id"] = row[1].As<std::string>();
        d["recipient_id"] = row[2].As<std::string>();
        d["package_id"] = row[3].As<std::string>();
        d["status"] = row[4].As<std::string>();
        d["address"] = row[5].As<std::string>();
        d["created_at"] = row[6].As<std::string>();
        arr.PushBack(d.ExtractValue());
    }
    return userver::formats::json::ToString(arr.ExtractValue());
}

}  // namespace

std::string GetDeliveriesHandler::HandleRequestThrow(
    const userver::server::http::HttpRequest& request,
    userver::server::request::RequestContext&) const {

    const auto token = AuthComponent::ExtractToken(request.GetHeader("Authorization"));
    auth_.ValidateToken(token);

    if (request.HasArg("sender_id")) {
        const auto result = pg_->Execute(
            userver::storages::postgres::ClusterHostType::kSlave,
            kDeliveryQuery + "sender_id = $1::uuid",
            request.GetArg("sender_id"));
        return BuildDeliveriesJson(result);
    }

    if (request.HasArg("recipient_id")) {
        const auto result = pg_->Execute(
            userver::storages::postgres::ClusterHostType::kSlave,
            kDeliveryQuery + "recipient_id = $1::uuid",
            request.GetArg("recipient_id"));
        return BuildDeliveriesJson(result);
    }

    throw userver::server::handlers::ClientError{};
}

}  // namespace delivery
