workspace "Delivery Service" "Variant 6: Parcel delivery management system" {
    properties {
        "dsl.theme" "default"
    }

    model {
        // 1. User roles (actors)
        customer = person "Customer" "Service user who sends or receives parcels" {
            tags "Actor"
        }

        // 2. External systems
        paymentSystem = softwareSystem "Payment System" "Отвечает за работу со сресдтвами пользователя" {
            tags "External"
        }
        notificationSystem = softwareSystem "Email" "Оповещает пользователя о статусах заказа" {
            tags "External"
        }

        // 3. Our main system with containers
        deliverySystem = softwareSystem "Delivery Service" "Allows users to create parcels and send them to each other." {
            tags "System"
            
            // 4. Containers
            webApp = container "Web Application (Frontend)" "Provides interface for interacting with the system" "React.js / Vue.js" {
                tags "Container:Frontend"
            }
            
            apiGateway = container "API Gateway (Backend)" "Handles HTTP requests, authentication, routing to microservices" "Golang" {
                tags "Container:Backend"
            }

            redis = container "Redis Cache" "Кеш для API GATEWAY" {
                tags "Cache"
            }

            kafka = container "Kafka message queue" "Очередь сообщений для асинхронной отправки писем" {
                tags "Queue"
            }
            
            userService = container "User Service" "Manages users (creation, search by login, search by name/surname pattern)" "С++ / Userver" {
                tags "Container:Backend"
            }
            
            parcelService = container "Parcel Service" "Manages parcels (creation, getting user's parcels)" "С++ / Userver" {
                tags "Container:Backend"
            }
            
            deliveryService = container "Delivery Service" "Manages deliveries (creation, search by sender/recipient), delivery business logic" "С++ / Userver" {
                tags "Container:Backend"
            }

            userDb = container "User Database" "Stores user data" "PostgreSQL" {
                tags "Container:Database"
            }
            
            parcelDb = container "Parcel Database" "Stores parcel data" "PostgreSQL" {
                tags "Container:Database"
            }
            
            deliveryDb = container "Delivery Database" "Stores delivery data (connection between parcel and recipient/sender)" "PostgreSQL" {
                tags "Container:Database"
            }
        }

        // 5. Relationships
        // Customer interactions
        customer -> webApp "Uses web interface" "HTTPS"
        customer -> deliverySystem "Uses" "HTTPS"
        
        // System to external systems
        deliverySystem -> paymentSystem "Requests payment/verification" "HTTPS/REST"
        // Container interactions
        webApp -> apiGateway "Sends requests" "HTTPS/REST"

        apiGateway -> redis "Ищет закешированные запросы пользователя""RESP"

        apiGateway -> userService "Forwards requests" "gRPC/HTTP"
        apiGateway -> parcelService "Forwards requests" "gRPC/HTTP"
        apiGateway -> deliveryService "Forwards requests" "gRPC/HTTP"

        userService -> userDb "CRUD operations" "JDBC/SQL"
        parcelService -> parcelDb "CRUD operations" "JDBC/SQL"
        deliveryService -> deliveryDb "CRUD operations" "JDBC/SQL"

        deliveryService -> parcelService "Get parcel information" "gRPC/HTTP"
        deliveryService -> userService "Verify user exists" "gRPC/HTTP"
        
        // Response relationships
        webApp -> customer "Displays information" "HTTPS"
        userDb -> userService "Returns data" "JDBC/SQL"
        parcelDb -> parcelService "Returns data" "JDBC/SQL"
        deliveryDb -> deliveryService "Returns data" "JDBC/SQL"
        paymentSystem -> deliveryService "Returns payment status" "HTTPS/REST"
        
        // Additional relationships for complete flow
        deliveryService -> apiGateway "Returns response" "gRPC/HTTP"
        apiGateway -> webApp "Returns response" "HTTPS/REST"

        deploymentEnvironment "PROD" {
                
            
            deploymentNode "app_tier" "Application Tier" "Kubernetes / Docker Swarm" "" {

                frontend = deploymentNode "frontend" "Frontend Instance" "React/Vue static files" {
                    webAppInstance = containerInstance webApp
                }
               api_gw =  deploymentNode "api_gateway_group" "API Gateway Cluster" "Horizontal scaling" "" {
                        apiGatewayInstance = containerInstance apiGateway
                }
                user_node = deploymentNode "user_service_group" "User Service Cluster" "Horizontal scaling" "" {
                    userServiceInstance = containerInstance userService
                }
                parcel_node = deploymentNode "parcel_service_group" "Parcel Service Cluster" "Horizontal scaling" "" {
                    parcelServiceInstance = containerInstance parcelService
                }
                delivery_node = deploymentNode "delivery_node" "Delivery Service Instance" "Go binary" {
                    deliveryServiceInstance = containerInstance deliveryService
                }
            }
            
            // Database tier
            deploymentNode "db_tier" "Database Tier" "Managed / Self-hosted" "" {
                
                // User DB cluster
                user_db_primary = deploymentNode "user_db_cluster" "User Database Cluster" "PostgreSQL" "" {
                    userDbPrimary = containerInstance userDb
                }
                
                // Parcel DB cluster
                parcel_db_primary = deploymentNode "parcel_db_cluster" "Parcel Database Cluster" "PostgreSQL" "" {
                    parcelDbPrimary = containerInstance parcelDb
                }
                
                // Delivery DB cluster
               delivery_db_primary =  deploymentNode "delivery_db_cluster" "Delivery Database Cluster" "PostgreSQL" "" {
                    deliveryDbPrimary = containerInstance deliveryDb
                }
            }
            
            // Cache tier
            redis_cache = deploymentNode "redis_cache" "Redis Cache" "In-memory cache"  ""{
                containerInstance redis
            }
        
            // Message queue
            kafka_queue = deploymentNode "message_queue" "Message Queue" "Async communication" "Queue" {
                containerInstance kafka
            }
            
            // External connections
            payment_node = deploymentNode "payment_gw" "Payment Gateway" "External service" "" {
                softwareSystemInstance paymentSystem
            }
            
            notification_node = deploymentNode "notification_node" "Notification Service" "External service" "" {
                softwareSystemInstance notificationSystem
            }
            
            // Customer access
            customer_node = deploymentNode "customer_device" "Customer Device" "Desktop / Mobile" "" {
                customerInstance = technology customer
            }
            
            // Relationships in production            
            frontend -> api_gw "API calls from browser" "HTTPS"

            api_gw -> redis_cache "Cache API gate away data" "Redis protocol"
            
            api_gw -> user_node "gRPC calls"
            api_gw -> parcel_node "gRPC calls"
            api_gw -> delivery_node "gRPC calls"
            
            delivery_node -> kafka_queue "Queue notification tasks" "AMQP"
            kafka_queue -> notification_node "Process notifications" "Async"
        }
    }

    views {
        // System Context diagram (C1)
        systemContext deliverySystem "C1" "Delivery system context" {
            include *
            autoLayout
        }

        // Container diagram (C2)
        container deliverySystem "C2" "Delivery system containers" {
            include *
            autoLayout
        }
        
        // 1 "Создание заказа"
        dynamic deliverySystem "CreateDeliveryFlow" "C3: Creating delivery from user to user (service flow)" {

            webApp -> apiGateway "1. Запрос на создание заказа"
            apiGateway -> deliveryService "2. POST /api/deliveries (delivery data)"

            deliveryService -> userService "3. Verifies sender and recipient exist (by ID/login)"
            userService -> userDb "4. SELECT users WHERE id IN (...)"
            userDb -> userService "5. Returns user data"
            userService -> deliveryService "6. Returns verification result"
            
            deliveryService -> parcelService "7. Creates parcel record (if not exists)"
            parcelService -> parcelDb "8. INSERT INTO parcels"
            parcelDb -> parcelService "9. Returns parcel ID"
            parcelService -> deliveryService "10. Returns parcel ID"
            
            deliveryService -> paymentSystem "11. Processes payment"
            paymentSystem -> deliveryService "12. Returns payment confirmation"
            
            deliveryService -> deliveryDb "13. INSERT INTO deliveries"
            deliveryDb -> deliveryService "14. Returns created delivery"
            
            autoLayout
        }
        
        
        // Dynamic diagram 2: "Create Delivery User Interaction" - using apiGateway as scope
        dynamic deliverySystem "CreateDeliveryUserInteraction" "C3: Creating delivery - user interaction flow" {
            // Show interactions from API Gateway perspective
            webApp -> apiGateway "1. POST /api/deliveries (delivery data)"
            
            apiGateway -> deliveryService "2. Forward create delivery request"
            deliveryService -> apiGateway "3. Return delivery creation result"
            
            apiGateway -> webApp "4. Return success response"
            
            autoLayout
        }
        
        // Dynamic diagram 3: "Find user by mask" - using userService as scope
        dynamic deliverySystem "FindUserByMask" "C3: Find user by name/surname mask" {
            // Show how user service handles search requests
            apiGateway -> userService "1. GET /users/search?mask=Ivan* (search by name/surname pattern)"
            userService -> userDb "2. SELECT * FROM users WHERE name LIKE 'Ivan%' OR surname LIKE 'Ivan%'"
            userDb -> userService "3. Returns matching users"
            userService -> apiGateway "4. Returns user list"
            
            autoLayout
        }
        
        // Dynamic diagram 4: "Get user's parcels" - using parcelService as scope
        dynamic deliverySystem "GetUserParcels" "C3: Get all parcels for a specific user" {
            apiGateway -> parcelService "1. GET /api/parcels?userId=123"
            parcelService -> parcelDb "2. SELECT * FROM parcels WHERE owner_id = 123"
            parcelDb -> parcelService "3. Returns parcels"
            parcelService -> apiGateway "4. Returns parcels list"
            
            autoLayout
        }


        deployment * "PROD" {
            include *
            autoLayout
            title "Схема развертывания в production"
        }
        


        // Styles configuration
        styles {
            element "Person" {
                shape Person
                background #ffcc00
                color #000000
            }
            element "Actor" {
                shape Person
                background #ffcc00
                color #000000
            }
            element "External" {
                shape RoundedBox
                background #9e9e9e
                color #ffffff
            }
            element "System" {
                background #1168bd
                color #ffffff
            }
            element "Container:Frontend" {
                shape WebBrowser
                background #6bb7d9
                color #000000
            }
            element "Container:Backend" {
                background #85bb5b
                color #000000
            }
            element "Container:Database" {
                shape Cylinder
                background #000000
                color #ffffff
            }
            element "Infrastructure Node" {
                shape Box
                background #ffffff
                border solid
            }
            element "Deployment Node" {
                shape Box
                background #ffffff
                border dashed
            }
            element "Queue"{
                shape Pipe
            }
        }
    }
}