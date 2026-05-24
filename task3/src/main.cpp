#include <userver/clients/dns/component.hpp>
#include <userver/components/minimal_server_component_list.hpp>
#include <userver/server/handlers/ping.hpp>
#include <userver/storages/postgres/component.hpp>
#include <userver/testsuite/testsuite_support.hpp>
#include <userver/utils/daemon_run.hpp>

#include "auth/auth_component.hpp"
#include "auth/login_handler.hpp"
#include "deliveries/create_delivery_handler.hpp"
#include "deliveries/get_deliveries_handler.hpp"
#include "packages/create_package_handler.hpp"
#include "packages/get_user_packages_handler.hpp"
#include "users/create_user_handler.hpp"
#include "users/search_users_handler.hpp"

int main(int argc, char* argv[]) {
    auto component_list =
        userver::components::MinimalServerComponentList()
            .Append<userver::server::handlers::Ping>()
            .Append<userver::clients::dns::Component>()
            .Append<userver::components::TestsuiteSupport>()
            .Append<userver::components::Postgres>("postgres-db-1")
            .Append<delivery::AuthComponent>()
            .Append<delivery::LoginHandler>()
            .Append<delivery::CreateUserHandler>()
            .Append<delivery::SearchUsersHandler>()
            .Append<delivery::CreatePackageHandler>()
            .Append<delivery::GetUserPackagesHandler>()
            .Append<delivery::CreateDeliveryHandler>()
            .Append<delivery::GetDeliveriesHandler>();

    return userver::utils::DaemonMain(argc, argv, component_list);
}
