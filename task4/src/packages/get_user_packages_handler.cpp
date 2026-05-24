#include "get_user_packages_handler.hpp"

#include <userver/components/component_context.hpp>
#include <userver/formats/bson/inline.hpp>
#include <userver/formats/json/serialize.hpp>
#include <userver/formats/json/value_builder.hpp>
#include <userver/storages/mongo/component.hpp>

namespace delivery {

namespace bson = userver::formats::bson;
namespace json = userver::formats::json;

GetUserPackagesHandler::GetUserPackagesHandler(
    const userver::components::ComponentConfig& config,
    const userver::components::ComponentContext& context)
    : HttpHandlerBase(config, context),
      auth_(context.FindComponent<AuthComponent>()),
      mongo_(context.FindComponent<userver::components::Mongo>("mongo-db-1").GetPool()) {}

std::string GetUserPackagesHandler::HandleRequestThrow(
    const userver::server::http::HttpRequest& request,
    userver::server::request::RequestContext&) const {

    auto token = AuthComponent::ExtractToken(request.GetHeader("Authorization"));
    auth_.ValidateToken(token);

    auto owner_id = bson::Oid{request.GetPathArg("id")};
    auto cursor   = mongo_->GetCollection("packages").Find(
        bson::MakeDoc("owner_id", owner_id)
    );

    json::ValueBuilder arr(userver::formats::common::Type::kArray);
    for (const auto& doc : cursor) {
        json::ValueBuilder pkg;
        pkg["id"]          = doc["_id"].As<bson::Oid>().ToString();
        pkg["owner_id"]    = doc["owner_id"].As<bson::Oid>().ToString();
        pkg["description"] = doc["description"].As<std::string>();
        pkg["weight"]      = doc["weight"].As<double>();
        pkg["status"]      = doc["status"].As<std::string>();
        arr.PushBack(pkg.ExtractValue());
    }
    return json::ToString(arr.ExtractValue());
}

}  // namespace delivery
