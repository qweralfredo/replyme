<?php

use PHPUnit\Framework\TestCase;

class KanbanApiTest extends TestCase
{
    private $client;
    
    protected function setUp(): void
    {
        // Use an HTTP Client or mock to test the API endpoint.
        // For local tests we can mock or use a built-in server.
        // Assuming we are going to test the logic directly or via local server.
        $this->client = new \GuzzleHttp\Client(['base_uri' => 'http://localhost:8080']);
    }

    public function testPatchWorkItemFailsWithInvalidStatus()
    {
        // ST1.1 RED: This should fail with 400 or 422 if status is invalid
        // We simulate a PATCH request to /api/work_item.php
        
        try {
            $response = $this->client->patch('/src/api/work_item.php', [
                'json' => [
                    'id' => 1,
                    'status' => 'INVALID_STATUS_THAT_DOES_NOT_EXIST'
                ]
            ]);
            
            // If it reaches here, it didn't fail. We force failure for RED.
            $this->fail("Expected an exception (400/422) but got " . $response->getStatusCode());
        } catch (\GuzzleHttp\Exception\ClientException $e) {
            $this->assertTrue(in_array($e->getResponse()->getStatusCode(), [400, 422]));
        }
    }
}
