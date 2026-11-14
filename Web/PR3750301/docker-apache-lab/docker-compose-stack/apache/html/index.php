<!DOCTYPE html>
<html lang="ca">
<head>
    <meta charset="UTF-8">
    <title>Stack LAMP amb Docker Compose</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
            margin: 0;
        }
        .container {
            max-width: 800px;
            margin: 0 auto;
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            padding: 40px;
            border-radius: 20px;
        }
        .status {
            padding: 20px;
            margin: 20px 0;
            border-radius: 10px;
            background: rgba(255, 255, 255, 0.2);
        }
        .success { border-left: 5px solid #2ecc71; }
        .error { border-left: 5px solid #e74c3c; }
        code {
            background: rgba(0, 0, 0, 0.3);
            padding: 2px 8px;
            border-radius: 3px;
        }
        table {
            width: 100%;
            margin: 20px 0;
            border-collapse: collapse;
        }
        th, td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid rgba(255, 255, 255, 0.2);
        }
        th { background: rgba(0, 0, 0, 0.3); }
    </style>
</head>
<body>
    <div class="container">
        <h1>🐳 Docker Compose: Apache + MySQL + phpMyAdmin</h1>

        <?php
	// connexió Redis
        try {
            $redis = new Redis();
            $redis->connect('redis', 6379, 2);

            // Incrementa el comptador de visites
            $visites = $redis->incr('visites:shaila');

            echo '<div class="status success">';
            echo '<h2>Shaila Martínez</h2>';
            echo '<h3>Comptador de visites amb Redis</h3>';
            echo '<p><strong>Nombre de visites:</strong> ' . $visites . '</p>';
            echo '</div>';

            $redis->close();

        } catch (RedisException $e) {
            echo '<div class="status error">';
            echo '<h3>Error de connexió a Redis</h3>';
            echo '<p>' . htmlspecialchars($e->getMessage()) . '</p>';
            echo '</div>';
        }



        // Configuració de la connexió a MySQL
        $host = 'mysql';  // Nom del servei en docker-compose.yml
        $user = 'root';
        $pass = 'rootpassword';
        $db = 'testdb';

        // Des de PHP 8.1, mysqli llança una excepció si falla la connexió;
        // la desactivem per poder mostrar el missatge d'error nosaltres
        mysqli_report(MYSQLI_REPORT_OFF);

        // Intenta connectar a MySQL
        $conn = @new mysqli($host, $user, $pass, $db);

        if ($conn->connect_error) {
            echo '<div class="status error">';
            echo '<h3>❌ Error de connexió a MySQL</h3>';
            echo '<p>' . $conn->connect_error . '</p>';
            echo '</div>';
        } else {
            echo '<div class="status success">';
            echo '<h3>✅ Connexió a MySQL establerta correctament</h3>';
            echo '<p><strong>Servidor:</strong> ' . $host . '</p>';
            echo '<p><strong>Base de dades:</strong> ' . $db . '</p>';

            // Mostra informació del servidor MySQL
            $version = $conn->query("SELECT VERSION() as version")->fetch_assoc();
            echo '<p><strong>Versió MySQL:</strong> ' . $version['version'] . '</p>';

            // Crea una taula de prova i insereix dades
            $conn->query("CREATE TABLE IF NOT EXISTS visits (
                id INT AUTO_INCREMENT PRIMARY KEY,
                timestamp DATETIME,
                ip_address VARCHAR(50)
            )");

            $ip = $_SERVER['REMOTE_ADDR'];
            $conn->query("INSERT INTO visits (timestamp, ip_address) VALUES (NOW(), '$ip')");

            // Mostra les últimes visites
            echo '<h3>📊 Últimes 5 visites registrades:</h3>';
            $result = $conn->query("SELECT * FROM visits ORDER BY timestamp DESC LIMIT 5");

            if ($result->num_rows > 0) {
                echo '<table>';
                echo '<tr><th>ID</th><th>Data i hora</th><th>IP</th></tr>';
                while($row = $result->fetch_assoc()) {
                    echo '<tr>';
                    echo '<td>' . $row['id'] . '</td>';
                    echo '<td>' . $row['timestamp'] . '</td>';
                    echo '<td>' . $row['ip_address'] . '</td>';
                    echo '</tr>';
                }
                echo '</table>';
            }

            echo '</div>';
            $conn->close();
        }
        ?>

        <div class="status">
            <h3>🔗 Enllaços útils:</h3>
            <p><a href="http://localhost:8091" style="color: #fff;">📊 phpMyAdmin</a> (usuari: root, contrasenya: rootpassword)</p>
            <p><strong>Info del sistema:</strong></p>
            <ul>
                <li>PHP versió: <?php echo phpversion(); ?></li>
                <li>Apache versió: <?php echo apache_get_version(); ?></li>
                <li>Contenidor: <?php echo gethostname(); ?></li>
            </ul>
        </div>

        <div class="status">
            <h3>📚 Conceptes demostrats:</h3>
            <ul>
                <li>✅ Multi-contenidor amb Docker Compose</li>
                <li>✅ Comunicació entre contenidors via xarxa Docker</li>
                <li>✅ Volums persistents per a MySQL</li>
                <li>✅ Variables d'entorn per a configuració</li>
                <li>✅ Dependències entre serveis (depends_on)</li>
            </ul>
        </div>
    </div>
</body>
</html>