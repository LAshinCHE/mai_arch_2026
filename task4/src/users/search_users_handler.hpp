#pragma once

#include <userver/server/handlers/http_handler_base.hpp>
#include <userver/storages/mongo/pool.hpp>

namespace delivery {

class SearchUsersHandler final : public userver::server::handlers::HttpHandlerBase {
public:
    static constexpr std::string_view kName = "handler-search-users";

    SearchUsersHandler(const userver::components::ComponentConfig&,
                       const userver::components::ComponentContext&);

    std::string HandleRequestThrow(
        const userver::server::http::HttpRequest&,
        userver::server::request::RequestContext&) const override;

private:
    userver::storages::mongo::PoolPtr mongo_;
};

}  // namespace delivery
