#include "auth_component.hpp"

#include <userver/components/component_context.hpp>
#include <userver/server/handlers/exceptions.hpp>
#include <userver/storages/postgres/component.hpp>

namespace delivery {

AuthComponent::AuthComponent(const userver::components::ComponentConfig& config,
                             const userver::components::ComponentContext& context)
    : ComponentBase(config, context),
      pg_(context.FindComponent<userver::components::Postgres>("postgres-db-1").GetCluster()) {}

std::string AuthComponent::ValidateToken(const std::string& token) const {
    const auto result = pg_->Execute(
        userver::storages::postgres::ClusterHostType::kSlave,
        "SELECT user_id::text FROM delivery.auth_tokens "
        "WHERE token = $1 AND expires_at > NOW()",
        token);

    if (result.IsEmpty()) {
        throw userver::server::handlers::Unauthorized{};
    }
    return result[0][0].As<std::string>();
}

std::string AuthComponent::ExtractToken(const std::string& auth_header) {
    if (auth_header.size() <= 7 || auth_header.substr(0, 7) != "Bearer ") {
        throw userver::server::handlers::Unauthorized{};
    }
    return auth_header.substr(7);
}

}  // namespace delivery
