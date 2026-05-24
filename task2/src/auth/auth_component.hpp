#pragma once

#include <string>
#include <userver/components/component_base.hpp>
#include <userver/storages/postgres/cluster.hpp>

namespace delivery {

class AuthComponent final : public userver::components::ComponentBase {
public:
    static constexpr std::string_view kName = "auth-component";

    AuthComponent(const userver::components::ComponentConfig& config,
                  const userver::components::ComponentContext& context);

    // Returns user_id if token is valid; throws Unauthorized if not.
    std::string ValidateToken(const std::string& token) const;

    // Parses "Bearer <token>" from Authorization header value.
    static std::string ExtractToken(const std::string& auth_header);

private:
    userver::storages::postgres::ClusterPtr pg_;
};

}  // namespace delivery
