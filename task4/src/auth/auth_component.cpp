#include "auth_component.hpp"

#include <chrono>
#include <userver/components/component_context.hpp>
#include <userver/formats/bson/inline.hpp>
#include <userver/server/handlers/exceptions.hpp>
#include <userver/storages/mongo/component.hpp>

namespace delivery {

namespace bson = userver::formats::bson;

AuthComponent::AuthComponent(const userver::components::ComponentConfig& config,
                             const userver::components::ComponentContext& context)
    : ComponentBase(config, context),
      mongo_(context.FindComponent<userver::components::Mongo>("mongo-db-1").GetPool()) {}

std::string AuthComponent::ValidateToken(const std::string& token) const {
    auto coll = mongo_->GetCollection("auth_tokens");
    auto now  = std::chrono::system_clock::now();
    auto doc  = coll.FindOne(bson::MakeDoc(
        "token", token,
        "expires_at", bson::MakeDoc("$gt", now)
    ));
    if (!doc) {
        throw userver::server::handlers::Unauthorized{};
    }
    return (*doc)["user_id"].As<bson::Oid>().ToString();
}

std::string AuthComponent::ExtractToken(const std::string& header) {
    if (header.size() <= 7 || header.substr(0, 7) != "Bearer ") {
        throw userver::server::handlers::Unauthorized{};
    }
    return header.substr(7);
}

}  // namespace delivery
