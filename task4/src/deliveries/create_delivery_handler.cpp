#include "create_delivery_handler.hpp"

#include <chrono>
#include <userver/components/component_context.hpp>
#include <userver/formats/bson/inline.hpp>
#include <userver/formats/json/serialize.hpp>
#include <userver/formats/json/value_builder.hpp>
#include <userver/server/handlers/exceptions.hpp>
#include <userver/server/http/http_status.hpp>
#include <userver/storages/mongo/component.hpp>

namespace delivery {

namespace bson = userver::formats::bson;
namespace json = userver::formats::json;

CreateDeliveryHandler::CreateDeliveryHandler(
    const userver::components::ComponentConfig& config,
    const userver::components::ComponentContext& context)
    : HttpHandlerBase(config, context),
      auth_(context.FindComponent<AuthComponent>()),
      mongo_(context.FindComponent<userver::components::Mongo>("mongo-db-1").GetPool()) {}

std::string CreateDeliveryHandler::HandleRequestThrow(
    const userver::server::http::HttpRequest& request,
    userver::server::request::RequestContext&) const {

    auto token = AuthComponent::ExtractToken(request.GetHeader("Authorization"));
    auth_.ValidateToken(token);

    auto body          = json::FromString(request.RequestBody());
    auto sender_str    = body["sender_id"].As<std::string>("");
    auto recipient_str = body["recipient_id"].As<std::string>("");
    auto package_str   = body["package_id"].As<std::string>("");
    auto address       = body["address"].As<std::string>("");

    if (sender_str.empty() || recipient_str.empty() || package_str.empty() || address.empty()) {
        throw userver::server::handlers::ClientError{};
    }

    bson::Oid sender_id, recipient_id, package_id;
    try {
        sender_id    = bson::Oid{sender_str};
        recipient_id = bson::Oid{recipient_str};
        package_id   = bson::Oid{package_str};
    } catch (const std::exception&) {
        throw userver::server::handlers::ClientError{};
    }

    auto id = bson::Oid{};
    mongo_->GetCollection("deliveries").InsertOne(bson::MakeDoc(
        "_id",          id,
        "sender_id",    sender_id,
        "recipient_id", recipient_id,
        "package_id",   package_id,
        "address",      address,
        "status",       std::string{"pending"},
        "created_at",   std::chrono::system_clock::now()
    ));

    request.GetHttpResponse().SetStatus(userver::server::http::HttpStatus::kCreated);
    json::ValueBuilder resp;
    resp["id"] = id.ToString();
    return json::ToString(resp.ExtractValue());
}

}  // namespace delivery
