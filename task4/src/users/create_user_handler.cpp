#include "create_user_handler.hpp"

#include <userver/components/component_context.hpp>
#include <userver/crypto/hash.hpp>
#include <userver/formats/bson/inline.hpp>
#include <userver/formats/json/serialize.hpp>
#include <userver/formats/json/value_builder.hpp>
#include <userver/server/handlers/exceptions.hpp>
#include <userver/server/http/http_status.hpp>
#include <userver/storages/mongo/component.hpp>
#include <userver/storages/mongo/exception.hpp>

namespace delivery {

namespace bson = userver::formats::bson;
namespace json = userver::formats::json;

CreateUserHandler::CreateUserHandler(const userver::components::ComponentConfig& config,
                                     const userver::components::ComponentContext& context)
    : HttpHandlerBase(config, context),
      mongo_(context.FindComponent<userver::components::Mongo>("mongo-db-1").GetPool()) {}

std::string CreateUserHandler::HandleRequestThrow(
    const userver::server::http::HttpRequest& request,
    userver::server::request::RequestContext&) const {

    auto body       = json::FromString(request.RequestBody());
    auto login      = body["login"].As<std::string>("");
    auto password   = body["password"].As<std::string>("");
    auto first_name = body["first_name"].As<std::string>("");
    auto last_name  = body["last_name"].As<std::string>("");
    auto email      = body["email"].As<std::string>("");

    if (login.empty() || password.empty() || first_name.empty() ||
        last_name.empty() || email.empty()) {
        throw userver::server::handlers::ClientError{};
    }

    auto id   = bson::Oid{};
    auto coll = mongo_->GetCollection("users");

    try {
        coll.InsertOne(bson::MakeDoc(
            "_id",           id,
            "login",         login,
            "password_hash", userver::crypto::hash::Sha256(password),
            "first_name",    first_name,
            "last_name",     last_name,
            "email",         email,
            "created_at",    std::chrono::system_clock::now()
        ));
    } catch (const userver::storages::mongo::DuplicateKeyException&) {
        request.GetHttpResponse().SetStatus(userver::server::http::HttpStatus::kConflict);
        return R"({"error":"user already exists"})";
    }

    request.GetHttpResponse().SetStatus(userver::server::http::HttpStatus::kCreated);
    json::ValueBuilder resp;
    resp["id"] = id.ToString();
    return json::ToString(resp.ExtractValue());
}

}  // namespace delivery
