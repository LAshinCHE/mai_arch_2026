workspace "Delivery Service" "Вариант 6: Система доставки" {

    model {
        customer = person "Customer" "Пользователь сервиса" {
            tags "Actor"
        }

        paymentSystem = softwareSystem "Payment System" "Отвечает за работу со сресдтвами пользователя" {
            tags "External"
        }
        notificationSystem = softwareSystem "Email" "Оповещает пользователя о статусах заказа" {
            tags "External"
        }

        deliverySystem = softwareSystem "Delivery Service" "Позволяет пользователям создавать посылки и отправлять их друг другу" {
            tags "System"
            
            webApp = container "Web Application (Frontend)" "Предоставляет интерфейс для взаимодействия с системой" "React.js / Vue.js" {
                tags "Container:Frontend"
            }
            

            redis = container "Redis Cache" "Кеш по доставкам" {
                tags "Cache"
            }

            // kafka = container "Kafka message queue" "Очередь сообщений для асинхронной отправки писем" {
            //     tags "Queue"
            // }
            
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

        customer -> webApp "Uses web interface" "HTTPS"
        customer -> deliverySystem "Uses" "HTTPS"
        
        deliverySystem -> paymentSystem "Проверка payment" "HTTPS/REST"
        deliveryService -> redis "Ищет закешированные запросы пользователя""RESP"


        userService -> userDb "CRUD" "JDBC/SQL"
        parcelService -> parcelDb "CRUD" "JDBC/SQL"
        deliveryService -> deliveryDb "CRUD" "JDBC/SQL"

        deliveryService -> parcelService "Get parcel information" "gRPC/HTTP"
        deliveryService -> userService "Проверка на наличие пользователя" "gRPC/HTTP"
        
        webApp -> customer "Информация о доставке" "HTTPS"
        userDb -> userService "Returns data" "JDBC/SQL"
        parcelDb -> parcelService "Returns data" "JDBC/SQL"
        deliveryDb -> deliveryService "Returns data" "JDBC/SQL"
        paymentSystem -> deliveryService "Returns payment status" "HTTPS/REST"

        deliveryService -> webApp "Returns response" "HTTPS/REST"
        webApp -> deliveryService "Create response"
        deliveryService -> notificationSystem "Отправка уведомлений о статусе заказа"
        notificationSystem -> customer "Чтение сообщений"
    
        deploymentEnvironment "PROD" {
    
            frontend = deploymentNode "frontend" "Frontend Instance" "React/Vue static files" {
                webAppInstance = containerInstance webApp
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
                
            user_db_primary = deploymentNode "user_db_cluster" "User Database Cluster" "PostgreSQL" "" {
                userDbPrimary = containerInstance userDb
            }
            
            parcel_db_primary = deploymentNode "parcel_db_cluster" "Parcel Database Cluster" "PostgreSQL" "" {
                parcelDbPrimary = containerInstance parcelDb
            }
            
            delivery_db_primary =  deploymentNode "delivery_db_cluster" "Delivery Database Cluster" "PostgreSQL" "" {
                deliveryDbPrimary = containerInstance deliveryDb
            }

            
            redis_cache = deploymentNode "redis_cache" "Redis Cache" "In-memory cache"  ""{
                containerInstance redis
            }
            payment_node = deploymentNode "payment_gw" "Payment Gateway" "External service" "" {
                softwareSystemInstance paymentSystem
            }
            
            notification_node = deploymentNode "notification_node" "Notification Service" "External service" "" {
                softwareSystemInstance notificationSystem
            }
            
            customer_node = deploymentNode "customer_device" "Customer Device" "Desktop / Mobile" "" {
                customerInstance = technology customer
            }
            

            delivery_node -> redis_cache "Cache API gate away data" "Redis protocol"
            
            delivery_node -> user_node "gRPC calls"
            delivery_node -> parcel_node "gRPC calls" 
        }
    }

    views {
        systemContext deliverySystem "C1" "Delivery system context" {
            include *
            autoLayout
        }

        container deliverySystem "C2" "Delivery system containers" {
            include *
            autoLayout
        }
        
        dynamic deliverySystem "CreateDeliveryFlow" "C3: Creating delivery from user to user (service flow)" {

            webApp -> deliveryService "1. Запрос на создание заказа"

            deliveryService -> userService "2. Verifies sender and recipient exist (by ID/login)"
            userService -> userDb "3. SELECT users WHERE id IN (...)"
            userDb -> userService "4. Returns user data"
            userService -> deliveryService "5. Returns verification result"
            
            deliveryService -> parcelService "6. Creates parcel record (if not exists)"
            parcelService -> parcelDb "7. INSERT INTO parcels"
            parcelDb -> parcelService "8. Returns parcel ID"
            parcelService -> deliveryService "9. Returns parcel ID"
            
            deliveryService -> paymentSystem "10. Processes payment"
            paymentSystem -> deliveryService "11. Returns payment confirmation"
            
            deliveryService -> deliveryDb "12. INSERT INTO deliveries"
            deliveryDb -> deliveryService "13. Returns created delivery"
            
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