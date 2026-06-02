<?php
require_once __DIR__ . '/ResponseFactory.php';
require_once __DIR__ . '/Database.php';

header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: GET, POST, PATCH, DELETE, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type');

if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    http_response_code(200);
    exit;
}

try {
    $pdo = Database::getInstance();
    $method = $_SERVER['REQUEST_METHOD'];

    if ($method === 'GET') {
        $stmt = $pdo->query("SELECT * FROM kanban_columns ORDER BY position ASC");
        ResponseFactory::json($stmt->fetchAll());
    } 
    elseif ($method === 'POST') {
        $input = json_decode(file_get_contents('php://input'), true);
        if (empty($input['status_key']) || empty($input['name'])) {
            ResponseFactory::error("Missing status_key or name", 400);
        }

        // Auto increment position if not provided
        $pos = $input['position'] ?? 99;
        
        $sql = "INSERT INTO kanban_columns (status_key, name, position, rule_category, rule_urgency, is_system) 
                VALUES (?, ?, ?, ?, ?, ?)";
        $stmt = $pdo->prepare($sql);
        $stmt->execute([
            $input['status_key'],
            $input['name'],
            $pos,
            $input['rule_category'] ?? null,
            $input['rule_urgency'] ?? null,
            0
        ]);
        ResponseFactory::json(['message' => 'Column created successfully']);
    }
    elseif ($method === 'DELETE') {
        $status_key = $_GET['status_key'] ?? '';
        if (empty($status_key)) {
            ResponseFactory::error("Missing status_key", 400);
        }

        // Check if system
        $stmt = $pdo->prepare("SELECT is_system FROM kanban_columns WHERE status_key = ?");
        $stmt->execute([$status_key]);
        $col = $stmt->fetch();

        if (!$col) {
            ResponseFactory::error("Column not found", 404);
        }
        if ($col['is_system']) {
            ResponseFactory::error("Cannot delete system column", 403);
        }

        $stmt = $pdo->prepare("DELETE FROM kanban_columns WHERE status_key = ?");
        $stmt->execute([$status_key]);
        ResponseFactory::json(['message' => 'Column deleted']);
    }
    else {
        ResponseFactory::error('Method not allowed', 405);
    }
} catch (\Exception $e) {
    ResponseFactory::error($e->getMessage(), 500);
}
