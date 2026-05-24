#include "create_package_handler.hpp"

#include <userver/components/component_context.hpp>
#include <userver/formats/json/serialize.hpp>
#include <userver/formats/json/value_builder.hpp>
#include <userver/server/handlers/exceptions.hpp>
#include <userver/server/http/http_status.hpp>
#include <userver/storages/postgres/component.hpp>

namespace delivery {

CreatePackageHandler::CreatePackageHandler(const userver::components::ComponentConfig& config,
                                           const userver::components::ComponentContext& context)
    : HttpHandlerBase(config, context),
      auth_(context.FindComponent<AuthComponent>()),
      pg_(context.FindComponent<userver::components::Postgres>("postgres-db-1").GetCluster()) {}

std::string CreatePackageHandler::HandleRequestThrow(
    const userver::server::http::HttpRequest& request,
    userver::server::request::RequestContext&) const {

    const auto token = AuthComponent::ExtractToken(request.GetHeader("Authorization"));
    const auto owner_id = auth_.ValidateToken(token);

    const auto body = userver::formats::json::FromString(request.RequestBody());
    const auto description = body["description"].As<std::string>("");
    const auto weight = body["weight"].As<double>(0.0);

    const auto result = pg_->Execute(
        userver::storages::postgres::ClusterHostType::kMaster,
        "INSERT INTO delivery.packages(owner_id, description, weight) "
        "VALUES($1::uuid, $2, $3) RETURNING id::text",
        owner_id, description, weight);

    request.GetHttpResponse().SetStatus(userver::server::http::HttpStatus::kCreated);

    userver::formats::json::ValueBuilder response;
    response["id"] = result[0][0].As<std::string>();
    return userver::formats::json::ToString(response.ExtractValue());
}

}  // namespace delivery
