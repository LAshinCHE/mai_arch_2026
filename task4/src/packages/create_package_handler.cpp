#include "create_package_handler.hpp"

#include <chrono>
#include <userver/components/component_context.hpp>
#include <userver/formats/bson/inline.hpp>
#include <userver/formats/json/serialize.hpp>
#include <userver/formats/json/value_builder.hpp>
#include <userver/server/http/http_status.hpp>
#include <userver/storages/mongo/component.hpp>

namespace delivery {

namespace bson = userver::formats::bson;
namespace json = userver::formats::json;

CreatePackageHandler::CreatePackageHandler(const userver::components::ComponentConfig& config,
                                           const userver::components::ComponentContext& context)
    : HttpHandlerBase(config, context),
      auth_(context.FindComponent<AuthComponent>()),
      mongo_(context.FindComponent<userver::components::Mongo>("mongo-db-1").GetPool()) {}

std::string CreatePackageHandler::HandleRequestThrow(
    const userver::server::http::HttpRequest& request,
    userver::server::request::RequestContext&) const {

    auto token    = AuthComponent::ExtractToken(request.GetHeader("Authorization"));
    auto owner_id = bson::Oid{auth_.ValidateToken(token)};

    auto body        = json::FromString(request.RequestBody());
    auto description = body["description"].As<std::string>("");
    auto weight      = body["weight"].As<double>(0.0);

    auto id = bson::Oid{};
    mongo_->GetCollection("packages").InsertOne(bson::MakeDoc(
        "_id",         id,
        "owner_id",    owner_id,
        "description", description,
        "weight",      weight,
        "status",      std::string{"created"},
        "created_at",  std::chrono::system_clock::now()
    ));

    request.GetHttpResponse().SetStatus(userver::server::http::HttpStatus::kCreated);
    json::ValueBuilder resp;
    resp["id"] = id.ToString();
    return json::ToString(resp.ExtractValue());
}

}  // namespace delivery
