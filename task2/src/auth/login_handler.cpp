#include "login_handler.hpp"

#include <userver/components/component_context.hpp>
#include <userver/crypto/hash.hpp>
#include <userver/formats/json/serialize.hpp>
#include <userver/formats/json/value_builder.hpp>
#include <userver/server/handlers/exceptions.hpp>
#include <userver/storages/postgres/component.hpp>
#include <userver/utils/uuid4.hpp>

namespace delivery {

LoginHandler::LoginHandler(const userver::components::ComponentConfig& config,
                           const userver::components::ComponentContext& context)
    : HttpHandlerBase(config, context),
      pg_(context.FindComponent<userver::components::Postgres>("postgres-db-1").GetCluster()) {}

std::string LoginHandler::HandleRequestThrow(
    const userver::server::http::HttpRequest& request,
    userver::server::request::RequestContext&) const {

    const auto body = userver::formats::json::FromString(request.RequestBody());
    const auto login = body["login"].As<std::string>("");
    const auto password = body["password"].As<std::string>("");

    if (login.empty() || password.empty()) {
        throw userver::server::handlers::ClientError{};
    }

    const auto password_hash = userver::crypto::hash::Sha256(password);

    const auto user_result = pg_->Execute(
        userver::storages::postgres::ClusterHostType::kSlave,
        "SELECT id::text FROM delivery.users WHERE login = $1 AND password_hash = $2",
        login, password_hash);

    if (user_result.IsEmpty()) {
        throw userver::server::handlers::Unauthorized{};
    }

    const auto user_id = user_result[0][0].As<std::string>();
    const auto token = userver::utils::generators::GenerateUuid();

    pg_->Execute(userver::storages::postgres::ClusterHostType::kMaster,
                 "INSERT INTO delivery.auth_tokens(token, user_id) VALUES($1, $2::uuid)",
                 token, user_id);

    userver::formats::json::ValueBuilder response;
    response["token"] = token;
    response["user_id"] = user_id;
    return userver::formats::json::ToString(response.ExtractValue());
}

}  // namespace delivery
