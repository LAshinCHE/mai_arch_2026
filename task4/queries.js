// mongosh mongodb://localhost:27017/delivery_db queries.js

const alice = db.users.findOne({ login: "alice" });
const bob   = db.users.findOne({ login: "bob" });

// CREATE

db.users.insertOne({
    login: "newuser",
    password_hash: "a665a45920422f9d417e4867efdc4fb8a04a1f3fff1fa07e998e86f7f7a27ae3",
    first_name: "New",
    last_name: "User",
    email: "new@example.com",
    created_at: new Date()
});

const pkg = db.packages.findOne({ owner_id: alice._id, status: "created" });

db.packages.insertOne({
    owner_id: alice._id,
    description: "Новая посылка",
    weight: 1.5,
    status: "created",
    created_at: new Date()
});

db.deliveries.insertOne({
    sender_id: alice._id,
    recipient_id: bob._id,
    package_id: pkg._id,
    address: "ул. Тестовая, д. 1, Москва",
    status: "pending",
    created_at: new Date()
});

// READ

db.users.findOne({ login: "alice" }, { password_hash: 0 });

// поиск по маске, регистронезависимо
db.users.find({
    first_name: { $regex: "ali", $options: "i" },
    last_name:  { $regex: "smi", $options: "i" }
}, { password_hash: 0 });

db.packages.find({ owner_id: alice._id });

db.packages.find({ status: { $in: ["created", "in_transit"] } });

db.packages.find({ weight: { $gt: 2.0 } });

db.deliveries.find({ recipient_id: bob._id });

db.deliveries.find({
    $or: [{ status: "pending" }, { status: "in_transit" }]
});

db.deliveries.find(
    { sender_id: alice._id },
    { _id: 1, recipient_id: 1, status: 1, address: 1 }
).sort({ created_at: -1 });

db.users.find({ last_name: { $regex: "ov$", $options: "i" } }, { login: 1, first_name: 1, last_name: 1 });

// UPDATE

db.packages.updateOne(
    { _id: pkg._id },
    { $set: { status: "in_transit" } }
);

db.deliveries.updateMany(
    { recipient_id: bob._id, status: "pending" },
    { $set: { status: "in_transit" } }
);

db.users.updateOne(
    { login: "alice" },
    { $set: { email: "alice.new@example.com" } }
);

// DELETE

db.auth_tokens.deleteMany({ expires_at: { $lt: new Date() } });

const monthAgo = new Date(Date.now() - 30 * 86400 * 1000);
db.packages.deleteMany({
    $and: [{ status: "cancelled" }, { created_at: { $lt: monthAgo } }]
});

db.users.deleteOne({ login: "newuser" });

// AGGREGATION

db.packages.aggregate([
    { $group: { _id: "$status", count: { $sum: 1 }, avg_weight: { $avg: "$weight" } } },
    { $sort: { count: -1 } }
]);

// топ-3 отправителя с join на users
db.deliveries.aggregate([
    { $match: { status: { $ne: "cancelled" } } },
    { $group: { _id: "$sender_id", deliveries: { $sum: 1 } } },
    { $sort: { deliveries: -1 } },
    { $limit: 3 },
    { $lookup: { from: "users", localField: "_id", foreignField: "_id", as: "user" } },
    { $unwind: "$user" },
    { $project: { login: "$user.login", first_name: "$user.first_name", deliveries: 1 } }
]);
