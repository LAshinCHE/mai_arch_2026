#include "get_deliveries_handler.hpp"

#include <userver/components/component_context.hpp>
#include <userver/formats/bson/inline.hpp>
#include <userver/formats/json/serialize.hpp>
#include <userver/formats/json/value_builder.hpp>
#include <userver/server/handlers/exceptions.hpp>
#include <userver/storages/mongo/component.hpp>

namespace delivery {

namespace bson = userver::formats::bson;
namespace json = userver::formats::json;

GetDeliveriesHandler::GetDeliveriesHandler(
    const userver::components::ComponentConfig& config,
    const userver::components::ComponentContext& context)
    : HttpHandlerBase(config, context),
      auth_(context.FindComponent<AuthComponent>()),
      mongo_(context.FindComponent<userver::components::Mongo>("mongo-db-1").GetPool()) {}

namespace {

std::string SerializeDeliveries(userver::storages::mongo::Cursor& cursor) {
    json::ValueBuilder arr(userver::formats::common::Type::kArray);
    for (const auto& doc : cursor) {
        json::ValueBuilder d;
        d["id"]           = doc["_id"].As<bson::Oid>().ToString();
        d["sender_id"]    = doc["sender_id"].As<bson::Oid>().ToString();
        d["recipient_id"] = doc["recipient_id"].As<bson::Oid>().ToString();
        d["package_id"]   = doc["package_id"].As<bson::Oid>().ToString();
        d["address"]      = doc["address"].As<std::string>();
        d["status"]       = doc["status"].As<std::string>();
        arr.PushBack(d.ExtractValue());
    }
    return json::ToString(arr.ExtractValue());
}

}  // namespace

std::string GetDeliveriesHandler::HandleRequestThrow(
    const userver::server::http::HttpRequest& request,
    userver::server::request::RequestContext&) const {

    auto token = AuthComponent::ExtractToken(request.GetHeader("Authorization"));
    auth_.ValidateToken(token);

    auto coll = mongo_->GetCollection("deliveries");

    if (request.HasArg("recipient_id")) {
        auto cursor = coll.Find(bson::MakeDoc(
            "recipient_id", bson::Oid{request.GetArg("recipient_id")}
        ));
        return SerializeDeliveries(cursor);
    }

    if (request.HasArg("sender_id")) {
        auto cursor = coll.Find(bson::MakeDoc(
            "sender_id", bson::Oid{request.GetArg("sender_id")}
        ));
        return SerializeDeliveries(cursor);
    }

    throw userver::server::handlers::ClientError{};
}

}  // namespace delivery
