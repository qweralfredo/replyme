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
        $stmt = $pdo->query("SELECT * FROM mcp_servers ORDER BY id ASC");
        ResponseFactory::json($stmt->fetchAll());
    } 
    elseif ($method === 'POST') {
        $input = json_decode(file_get_contents('php://input'), true);
        if (empty($input['name']) || (empty($input['url']) && empty($input['command']))) {
            ResponseFactory::error("Missing name or url/command", 400);
        }
        
        $url = $input['url'] ?? '';
        $command = $input['command'] ?? '';

        if (!empty($command)) {
            $sql = "INSERT INTO mcp_servers (name, url, status, inferred_command, created_at) VALUES (?, ?, 'installed', ?, CURRENT_TIMESTAMP)";
            $stmt = $pdo->prepare($sql);
            $stmt->execute([
                $input['name'],
                $url,
                $command
            ]);
            ResponseFactory::json(['message' => 'MCP Server cadastrado localmente', 'id' => $pdo->lastInsertId()]);
        } else {
            $sql = "INSERT INTO mcp_servers (name, url, status, created_at) VALUES (?, ?, 'pending', CURRENT_TIMESTAMP)";
            $stmt = $pdo->prepare($sql);
            $stmt->execute([
                $input['name'],
                $url
            ]);
            ResponseFactory::json(['message' => 'MCP Server queued for installation', 'id' => $pdo->lastInsertId()]);
        }
    }
    elseif ($method === 'DELETE') {
        $id = $_GET['id'] ?? '';
        if (empty($id)) {
            ResponseFactory::error("Missing id", 400);
        }

        $stmt = $pdo->prepare("DELETE FROM mcp_servers WHERE id = ?");
        $stmt->execute([$id]);
        ResponseFactory::json(['message' => 'MCP Server deleted']);
    }
    else {
        ResponseFactory::error('Method not allowed', 405);
    }
} catch (\Exception $e) {
    ResponseFactory::error($e->getMessage(), 500);
}
