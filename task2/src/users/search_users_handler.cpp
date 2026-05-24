#include "search_users_handler.hpp"

#include <userver/components/component_context.hpp>
#include <userver/formats/json/serialize.hpp>
#include <userver/formats/json/value_builder.hpp>
#include <userver/server/handlers/exceptions.hpp>
#include <userver/storages/postgres/component.hpp>

namespace delivery {

SearchUsersHandler::SearchUsersHandler(const userver::components::ComponentConfig& config,
                                       const userver::components::ComponentContext& context)
    : HttpHandlerBase(config, context),
      pg_(context.FindComponent<userver::components::Postgres>("postgres-db-1").GetCluster()) {}

namespace {

std::string BuildUsersJson(const userver::storages::postgres::ResultSet& result) {
    userver::formats::json::ValueBuilder arr(userver::formats::common::Type::kArray);
    for (const auto& row : result) {
        userver::formats::json::ValueBuilder user;
        user["id"] = row[0].As<std::string>();
        user["login"] = row[1].As<std::string>();
        user["first_name"] = row[2].As<std::string>();
        user["last_name"] = row[3].As<std::string>();
        user["email"] = row[4].As<std::string>();
        arr.PushBack(user.ExtractValue());
    }
    return userver::formats::json::ToString(arr.ExtractValue());
}

}  // namespace

std::string SearchUsersHandler::HandleRequestThrow(
    const userver::server::http::HttpRequest& request,
    userver::server::request::RequestContext&) const {

    if (request.HasArg("login")) {
        const auto result = pg_->Execute(
            userver::storages::postgres::ClusterHostType::kSlave,
            "SELECT id::text, login, first_name, last_name, email "
            "FROM delivery.users WHERE login = $1",
            request.GetArg("login"));
        return BuildUsersJson(result);
    }

    if (request.HasArg("name")) {
        const auto first_name = "%" + request.GetArg("name") + "%";
        const auto last_name = "%" + request.GetArg("last_name") + "%";
        const auto result = pg_->Execute(
            userver::storages::postgres::ClusterHostType::kSlave,
            "SELECT id::text, login, first_name, last_name, email "
            "FROM delivery.users "
            "WHERE first_name ILIKE $1 AND last_name ILIKE $2",
            first_name, last_name);
        return BuildUsersJson(result);
    }

    throw userver::server::handlers::ClientError{};
}

}  // namespace delivery
