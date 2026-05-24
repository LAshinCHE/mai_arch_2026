#include "login_handler.hpp"

#include <chrono>
#include <userver/components/component_context.hpp>
#include <userver/crypto/hash.hpp>
#include <userver/formats/bson/inline.hpp>
#include <userver/formats/json/serialize.hpp>
#include <userver/formats/json/value_builder.hpp>
#include <userver/server/handlers/exceptions.hpp>
#include <userver/storages/mongo/component.hpp>
#include <userver/utils/uuid4.hpp>

namespace delivery {

namespace bson = userver::formats::bson;
namespace json = userver::formats::json;

LoginHandler::LoginHandler(const userver::components::ComponentConfig& config,
                           const userver::components::ComponentContext& context)
    : HttpHandlerBase(config, context),
      mongo_(context.FindComponent<userver::components::Mongo>("mongo-db-1").GetPool()) {}

std::string LoginHandler::HandleRequestThrow(
    const userver::server::http::HttpRequest& request,
    userver::server::request::RequestContext&) const {

    auto body     = json::FromString(request.RequestBody());
    auto login    = body["login"].As<std::string>("");
    auto password = body["password"].As<std::string>("");

    if (login.empty() || password.empty()) {
        throw userver::server::handlers::ClientError{};
    }

    auto users = mongo_->GetCollection("users");
    auto user  = users.FindOne(bson::MakeDoc(
        "login", login,
        "password_hash", userver::crypto::hash::Sha256(password)
    ));

    if (!user) {
        throw userver::server::handlers::Unauthorized{};
    }

    auto user_id = (*user)["_id"].As<bson::Oid>();
    auto token   = userver::utils::generators::GenerateUuid();
    auto now     = std::chrono::system_clock::now();

    mongo_->GetCollection("auth_tokens").InsertOne(bson::MakeDoc(
        "token",      token,
        "user_id",    user_id,
        "created_at", now,
        "expires_at", now + std::chrono::hours(24)
    ));

    json::ValueBuilder resp;
    resp["token"]   = token;
    resp["user_id"] = user_id.ToString();
    return json::ToString(resp.ExtractValue());
}

}  // namespace delivery
