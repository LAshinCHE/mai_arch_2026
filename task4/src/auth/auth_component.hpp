#pragma once

#include <string>
#include <userver/components/component_base.hpp>
#include <userver/storages/mongo/pool.hpp>

namespace delivery {

class AuthComponent final : public userver::components::ComponentBase {
public:
    static constexpr std::string_view kName = "auth-component";

    AuthComponent(const userver::components::ComponentConfig&,
                  const userver::components::ComponentContext&);

    std::string ValidateToken(const std::string& token) const;
    static std::string ExtractToken(const std::string& auth_header);

private:
    userver::storages::mongo::PoolPtr mongo_;
};

}  // namespace delivery
