// mongosh mongodb://localhost:27017/delivery_db data.js

if (db.users.countDocuments() > 0) {
    print("data already loaded, skipping");
    quit(0);
}

// SHA-256 хэши паролей: alice=secret, bob=12345, charlie=1, остальные=pass
const H = {
    secret:  "2bb80d537b1da3e38bd30361aa855686bde0eacd7162fef6a25fe97bf527a25b",
    "12345": "5994471abb01112afcc18159f6cc74b4f511b99806da59b3caf5a9c173cacfc5",
    "1":     "6b86b273ff34fce19d6b804eff5a3f5747ada4eaa22f1d49c01e52ddb7875b4b",
    pass:    "d74ff0ee8da3b9806b18c877dbf29bbde50b5bd8e4dad7a3a725000feb82e8f1",
};

const userIds = Array.from({ length: 12 }, () => new ObjectId());
const pkgIds  = Array.from({ length: 12 }, () => new ObjectId());

db.users.insertMany([
    { _id: userIds[0],  login: "alice",   password_hash: H.secret,  first_name: "Alice",   last_name: "Smith",    email: "alice@example.com",   created_at: new Date("2024-01-10") },
    { _id: userIds[1],  login: "bob",     password_hash: H["12345"],first_name: "Bob",     last_name: "Johnson",  email: "bob@example.com",     created_at: new Date("2024-01-11") },
    { _id: userIds[2],  login: "charlie", password_hash: H["1"],    first_name: "Charlie", last_name: "Brown",    email: "charlie@example.com", created_at: new Date("2024-01-12") },
    { _id: userIds[3],  login: "diana",   password_hash: H.pass,    first_name: "Diana",   last_name: "Ivanova",  email: "diana@example.com",   created_at: new Date("2024-01-13") },
    { _id: userIds[4],  login: "eve",     password_hash: H.pass,    first_name: "Eve",     last_name: "Petrova",  email: "eve@example.com",     created_at: new Date("2024-01-14") },
    { _id: userIds[5],  login: "frank",   password_hash: H.pass,    first_name: "Frank",   last_name: "Sidorov",  email: "frank@example.com",   created_at: new Date("2024-01-15") },
    { _id: userIds[6],  login: "grace",   password_hash: H.pass,    first_name: "Grace",   last_name: "Kozlova",  email: "grace@example.com",   created_at: new Date("2024-01-16") },
    { _id: userIds[7],  login: "henry",   password_hash: H.pass,    first_name: "Henry",   last_name: "Novikov",  email: "henry@example.com",   created_at: new Date("2024-01-17") },
    { _id: userIds[8],  login: "ivan",    password_hash: H.pass,    first_name: "Ivan",    last_name: "Alexeyev", email: "ivan@example.com",    created_at: new Date("2024-01-18") },
    { _id: userIds[9],  login: "julia",   password_hash: H.pass,    first_name: "Julia",   last_name: "Smirnova", email: "julia@example.com",   created_at: new Date("2024-01-19") },
    { _id: userIds[10], login: "kevin",   password_hash: H.pass,    first_name: "Kevin",   last_name: "Morozov",  email: "kevin@example.com",   created_at: new Date("2024-01-20") },
    { _id: userIds[11], login: "lisa",    password_hash: H.pass,    first_name: "Lisa",    last_name: "Volkova",  email: "lisa@example.com",    created_at: new Date("2024-01-21") },
]);

db.packages.insertMany([
    { _id: pkgIds[0],  owner_id: userIds[0], description: "Книги по программированию", weight: 2.5,  status: "created",    created_at: new Date("2024-02-01") },
    { _id: pkgIds[1],  owner_id: userIds[0], description: "Ноутбук Lenovo",             weight: 1.8,  status: "in_transit", created_at: new Date("2024-02-02") },
    { _id: pkgIds[2],  owner_id: userIds[1], description: "Зимняя одежда",              weight: 3.2,  status: "delivered",  created_at: new Date("2024-02-03") },
    { _id: pkgIds[3],  owner_id: userIds[1], description: "Запчасти для велосипеда",    weight: 0.75, status: "created",    created_at: new Date("2024-02-04") },
    { _id: pkgIds[4],  owner_id: userIds[2], description: "Samsung Galaxy S23",         weight: 0.2,  status: "in_transit", created_at: new Date("2024-02-05") },
    { _id: pkgIds[5],  owner_id: userIds[3], description: "Продукты",                   weight: 5.0,  status: "created",    created_at: new Date("2024-02-06") },
    { _id: pkgIds[6],  owner_id: userIds[4], description: "Детские игрушки",            weight: 1.2,  status: "delivered",  created_at: new Date("2024-02-07") },
    { _id: pkgIds[7],  owner_id: userIds[5], description: "Документы",                  weight: 0.3,  status: "created",    created_at: new Date("2024-02-08") },
    { _id: pkgIds[8],  owner_id: userIds[6], description: "Косметика",                  weight: 0.5,  status: "in_transit", created_at: new Date("2024-02-09") },
    { _id: pkgIds[9],  owner_id: userIds[7], description: "Садовые инструменты",        weight: 4.7,  status: "created",    created_at: new Date("2024-02-10") },
    { _id: pkgIds[10], owner_id: userIds[8], description: "Чайник",                     weight: 1.1,  status: "cancelled",  created_at: new Date("2024-02-11") },
    { _id: pkgIds[11], owner_id: userIds[9], description: "Учебники",                   weight: 3.8,  status: "created",    created_at: new Date("2024-02-12") },
]);

db.deliveries.insertMany([
    { sender_id: userIds[0],  recipient_id: userIds[1],  package_id: pkgIds[0],  status: "pending",    address: "ул. Ленина, д. 10, Москва",           created_at: new Date("2024-03-01") },
    { sender_id: userIds[1],  recipient_id: userIds[2],  package_id: pkgIds[2],  status: "delivered",  address: "пр. Мира, д. 5, Санкт-Петербург",     created_at: new Date("2024-03-02") },
    { sender_id: userIds[2],  recipient_id: userIds[3],  package_id: pkgIds[4],  status: "in_transit", address: "ул. Садовая, д. 3, Казань",            created_at: new Date("2024-03-03") },
    { sender_id: userIds[0],  recipient_id: userIds[4],  package_id: pkgIds[1],  status: "in_transit", address: "ул. Пушкина, д. 7, Новосибирск",       created_at: new Date("2024-03-04") },
    { sender_id: userIds[3],  recipient_id: userIds[5],  package_id: pkgIds[5],  status: "pending",    address: "пр. Победы, д. 15, Екатеринбург",     created_at: new Date("2024-03-05") },
    { sender_id: userIds[4],  recipient_id: userIds[6],  package_id: pkgIds[6],  status: "delivered",  address: "ул. Гагарина, д. 2, Нижний Новгород",  created_at: new Date("2024-03-06") },
    { sender_id: userIds[5],  recipient_id: userIds[7],  package_id: pkgIds[7],  status: "pending",    address: "ул. Советская, д. 44, Самара",          created_at: new Date("2024-03-07") },
    { sender_id: userIds[6],  recipient_id: userIds[8],  package_id: pkgIds[8],  status: "in_transit", address: "ул. Кирова, д. 8, Омск",               created_at: new Date("2024-03-08") },
    { sender_id: userIds[7],  recipient_id: userIds[9],  package_id: pkgIds[9],  status: "pending",    address: "пр. Ленина, д. 100, Челябинск",        created_at: new Date("2024-03-09") },
    { sender_id: userIds[8],  recipient_id: userIds[0],  package_id: pkgIds[10], status: "cancelled",  address: "ул. Мира, д. 30, Красноярск",           created_at: new Date("2024-03-10") },
    { sender_id: userIds[9],  recipient_id: userIds[1],  package_id: pkgIds[11], status: "pending",    address: "ул. Цветочная, д. 5, Уфа",             created_at: new Date("2024-03-11") },
    { sender_id: userIds[10], recipient_id: userIds[11], package_id: pkgIds[3],  status: "in_transit", address: "ул. Новая, д. 12, Воронеж",             created_at: new Date("2024-03-12") },
]);

const now    = new Date();
const future = new Date(now.getTime() + 86400 * 1000 * 30);

db.auth_tokens.insertMany([
    { token: "test-token-alice",   user_id: userIds[0], created_at: now, expires_at: future },
    { token: "test-token-bob",     user_id: userIds[1], created_at: now, expires_at: future },
    { token: "test-token-charlie", user_id: userIds[2], created_at: now, expires_at: future },
]);

print("users: "       + db.users.countDocuments());
print("packages: "    + db.packages.countDocuments());
print("deliveries: "  + db.deliveries.countDocuments());
print("auth_tokens: " + db.auth_tokens.countDocuments());
