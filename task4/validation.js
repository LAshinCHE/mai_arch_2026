// mongosh mongodb://localhost:27017/delivery_db validation.js

db.createCollection("users", {
    validator: {
        $jsonSchema: {
            bsonType: "object",
            required: ["login", "password_hash", "first_name", "last_name", "email", "created_at"],
            properties: {
                login: {
                    bsonType: "string",
                    minLength: 1,
                    maxLength: 64,
                    pattern: "^[a-zA-Z0-9_]+$"
                },
                password_hash: {
                    bsonType: "string",
                    minLength: 64,
                    maxLength: 64
                },
                first_name:  { bsonType: "string", minLength: 1 },
                last_name:   { bsonType: "string", minLength: 1 },
                email:       { bsonType: "string", pattern: ".+@.+" },
                created_at:  { bsonType: "date" }
            }
        }
    },
    validationLevel: "strict",
    validationAction: "error"
});

db.createCollection("packages", {
    validator: {
        $jsonSchema: {
            bsonType: "object",
            required: ["owner_id", "description", "weight", "status", "created_at"],
            properties: {
                owner_id:    { bsonType: "objectId" },
                description: { bsonType: "string" },
                weight:      { bsonType: ["double", "int", "long"], minimum: 0 },
                status:      { bsonType: "string", enum: ["created", "in_transit", "delivered", "cancelled"] },
                created_at:  { bsonType: "date" }
            }
        }
    }
});

db.createCollection("deliveries", {
    validator: {
        $jsonSchema: {
            bsonType: "object",
            required: ["sender_id", "recipient_id", "package_id", "address", "status", "created_at"],
            properties: {
                sender_id:    { bsonType: "objectId" },
                recipient_id: { bsonType: "objectId" },
                package_id:   { bsonType: "objectId" },
                address:      { bsonType: "string", minLength: 1 },
                status:       { bsonType: "string", enum: ["pending", "in_transit", "delivered", "cancelled"] },
                created_at:   { bsonType: "date" }
            }
        }
    }
});

db.createCollection("auth_tokens");

db.users.createIndex({ login: 1 }, { unique: true });
db.users.createIndex({ email: 1 }, { unique: true });
db.users.createIndex({ first_name: 1, last_name: 1 });
db.packages.createIndex({ owner_id: 1 });
db.packages.createIndex({ status: 1 });
db.deliveries.createIndex({ sender_id: 1 });
db.deliveries.createIndex({ recipient_id: 1 });
db.deliveries.createIndex({ created_at: -1 });
db.auth_tokens.createIndex({ token: 1 }, { unique: true });
db.auth_tokens.createIndex({ expires_at: 1 }, { expireAfterSeconds: 0 }); // TTL

print("collections and indexes created");

// тесты валидации
try {
    db.users.insertOne({ login: "", password_hash: "x", first_name: "A", last_name: "B", email: "a@b.com", created_at: new Date() });
    print("FAIL: empty login should have been rejected");
} catch (e) {
    print("ok: empty login rejected");
}

try {
    db.users.insertOne({ login: "ok", password_hash: "short", first_name: "A", last_name: "B", email: "a@b.com", created_at: new Date() });
    print("FAIL: short hash should have been rejected");
} catch (e) {
    print("ok: short password_hash rejected");
}

try {
    db.users.insertOne({ login: "ok2", password_hash: "a".repeat(64), first_name: "A", last_name: "B", email: "notanemail", created_at: new Date() });
    print("FAIL: invalid email should have been rejected");
} catch (e) {
    print("ok: invalid email rejected");
}

try {
    db.packages.insertOne({ owner_id: new ObjectId(), description: "x", weight: -1.0, status: "created", created_at: new Date() });
    print("FAIL: negative weight should have been rejected");
} catch (e) {
    print("ok: negative weight rejected");
}

try {
    db.packages.insertOne({ owner_id: new ObjectId(), description: "x", weight: 1.0, status: "flying", created_at: new Date() });
    print("FAIL: unknown status should have been rejected");
} catch (e) {
    print("ok: unknown status rejected");
}
