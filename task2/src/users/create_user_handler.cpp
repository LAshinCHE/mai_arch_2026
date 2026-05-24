#include "create_user_handler.hpp"

#include <userver/components/component_context.hpp>
#include <userver/crypto/hash.hpp>
#include <userver/formats/json/serialize.hpp>
#include <userver/formats/json/value_builder.hpp>
#include <userver/server/handlers/exceptions.hpp>
#include <userver/server/http/http_status.hpp>
#include <userver/storages/postgres/component.hpp>
#include <userver/storages/postgres/exceptions.hpp>

namespace delivery {

CreateUserHandler::CreateUserHandler(const userver::components::ComponentConfig& config,
                                     const userver::components::ComponentContext& context)
    : HttpHandlerBase(config, context),
      pg_(context.FindComponent<userver::components::Postgres>("postgres-db-1").GetCluster()) {}

std::string CreateUserHandler::HandleRequestThrow(
    const userver::server::http::HttpRequest& request,
    userver::server::request::RequestContext&) const {

    const auto body = userver::formats::json::FromString(request.RequestBody());
    const auto login = body["login"].As<std::string>("");
    const auto password = body["password"].As<std::string>("");
    const auto first_name = body["first_name"].As<std::string>("");
    const auto last_name = body["last_name"].As<std::string>("");
    const auto email = body["email"].As<std::string>("");

    if (login.empty() || password.empty() || first_name.empty() ||
        last_name.empty() || email.empty()) {
        throw userver::server::handlers::ClientError{};
    }

    const auto password_hash = userver::crypto::hash::Sha256(password);

    std::string user_id;
    try {
        const auto result = pg_->Execute(
            userver::storages::postgres::ClusterHostType::kMaster,
            "INSERT INTO delivery.users(login, password_hash, first_name, last_name, email) "
            "VALUES($1, $2, $3, $4, $5) RETURNING id::text",
            login, password_hash, first_name, last_name, email);
        user_id = result[0][0].As<std::string>();
    } catch (const userver::storages::postgres::UniqueViolation&) {
        request.GetHttpResponse().SetStatus(userver::server::http::HttpStatus::kConflict);
        return R"({"error":"user with this login already exists"})";
    }

    request.GetHttpResponse().SetStatus(userver::server::http::HttpStatus::kCreated);

    userver::formats::json::ValueBuilder response;
    response["id"] = user_id;
    return userver::formats::json::ToString(response.ExtractValue());
}

}  // namespace delivery
