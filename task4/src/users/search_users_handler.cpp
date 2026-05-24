#include "search_users_handler.hpp"

#include <userver/components/component_context.hpp>
#include <userver/formats/bson/inline.hpp>
#include <userver/formats/json/serialize.hpp>
#include <userver/formats/json/value_builder.hpp>
#include <userver/server/handlers/exceptions.hpp>
#include <userver/storages/mongo/component.hpp>

namespace delivery {

namespace bson = userver::formats::bson;
namespace json = userver::formats::json;

SearchUsersHandler::SearchUsersHandler(const userver::components::ComponentConfig& config,
                                       const userver::components::ComponentContext& context)
    : HttpHandlerBase(config, context),
      mongo_(context.FindComponent<userver::components::Mongo>("mongo-db-1").GetPool()) {}

namespace {

std::string SerializeUsers(userver::storages::mongo::Cursor& cursor) {
    json::ValueBuilder arr(userver::formats::common::Type::kArray);
    for (const auto& doc : cursor) {
        json::ValueBuilder u;
        u["id"]         = doc["_id"].As<bson::Oid>().ToString();
        u["login"]      = doc["login"].As<std::string>();
        u["first_name"] = doc["first_name"].As<std::string>();
        u["last_name"]  = doc["last_name"].As<std::string>();
        u["email"]      = doc["email"].As<std::string>();
        arr.PushBack(u.ExtractValue());
    }
    return json::ToString(arr.ExtractValue());
}

}  // namespace

std::string SearchUsersHandler::HandleRequestThrow(
    const userver::server::http::HttpRequest& request,
    userver::server::request::RequestContext&) const {

    auto coll = mongo_->GetCollection("users");

    if (request.HasArg("login")) {
        auto cursor = coll.Find(bson::MakeDoc("login", request.GetArg("login")));
        return SerializeUsers(cursor);
    }

    if (request.HasArg("name")) {
        auto cursor = coll.Find(bson::MakeDoc(
            "first_name", bson::MakeDoc("$regex", request.GetArg("name"), "$options", "i"),
            "last_name",  bson::MakeDoc("$regex", request.GetArg("last_name"), "$options", "i")
        ));
        return SerializeUsers(cursor);
    }

    throw userver::server::handlers::ClientError{};
}

}  // namespace delivery
