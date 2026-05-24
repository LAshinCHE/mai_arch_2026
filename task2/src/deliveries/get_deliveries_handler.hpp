#pragma once

#include "auth/auth_component.hpp"
#include <userver/server/handlers/http_handler_base.hpp>
#include <userver/storages/postgres/cluster.hpp>

namespace delivery {

class GetDeliveriesHandler final : public userver::server::handlers::HttpHandlerBase {
public:
    static constexpr std::string_view kName = "handler-get-deliveries";

    GetDeliveriesHandler(const userver::components::ComponentConfig& config,
                         const userver::components::ComponentContext& context);

    std::string HandleRequestThrow(
        const userver::server::http::HttpRequest& request,
        userver::server::request::RequestContext& context) const override;

private:
    AuthComponent& auth_;
    userver::storages::postgres::ClusterPtr pg_;
};

}  // namespace delivery
