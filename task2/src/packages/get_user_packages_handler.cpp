#include "get_user_packages_handler.hpp"

#include <userver/components/component_context.hpp>
#include <userver/formats/json/serialize.hpp>
#include <userver/formats/json/value_builder.hpp>
#include <userver/storages/postgres/component.hpp>

namespace delivery {

GetUserPackagesHandler::GetUserPackagesHandler(
    const userver::components::ComponentConfig& config,
    const userver::components::ComponentContext& context)
    : HttpHandlerBase(config, context),
      auth_(context.FindComponent<AuthComponent>()),
      pg_(context.FindComponent<userver::components::Postgres>("postgres-db-1").GetCluster()) {}

std::string GetUserPackagesHandler::HandleRequestThrow(
    const userver::server::http::HttpRequest& request,
    userver::server::request::RequestContext&) const {

    const auto token = AuthComponent::ExtractToken(request.GetHeader("Authorization"));
    auth_.ValidateToken(token);

    const auto owner_id = request.GetPathArg("id");

    const auto result = pg_->Execute(
        userver::storages::postgres::ClusterHostType::kSlave,
        "SELECT id::text, owner_id::text, description, weight::text, status, "
        "       created_at::text "
        "FROM delivery.packages WHERE owner_id = $1::uuid",
        owner_id);

    userver::formats::json::ValueBuilder arr(userver::formats::common::Type::kArray);
    for (const auto& row : result) {
        userver::formats::json::ValueBuilder pkg;
        pkg["id"] = row[0].As<std::string>();
        pkg["owner_id"] = row[1].As<std::string>();
        pkg["description"] = row[2].As<std::string>();
        pkg["weight"] = row[3].As<std::string>();
        pkg["status"] = row[4].As<std::string>();
        pkg["created_at"] = row[5].As<std::string>();
        arr.PushBack(pkg.ExtractValue());
    }
    return userver::formats::json::ToString(arr.ExtractValue());
}

}  // namespace delivery
