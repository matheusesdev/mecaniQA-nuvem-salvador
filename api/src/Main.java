import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;
import java.io.OutputStream;
import java.net.InetSocketAddress;
import java.net.ServerSocket;
import java.net.Socket;
import java.nio.charset.StandardCharsets;

public final class Main {
    private static final int PORT = 8080;
    private static final String DB_HOST = environment("DB_HOST", "localhost");
    private static final int DB_PORT = environmentPort("DB_PORT", 3306);
    private static final String REDIS_HOST = environment("REDIS_HOST", "localhost");
    private static final int REDIS_PORT = environmentPort("REDIS_PORT", 6379);
    private static final int CONNECTION_TIMEOUT_MS = 2_000;
    private static final byte[] NOT_FOUND_RESPONSE =
            "{\"status\":\"NOT_FOUND\"}".getBytes(StandardCharsets.UTF_8);

    private Main() {
    }

    public static void main(String[] args) throws IOException {
        try (ServerSocket server = new ServerSocket(PORT)) {
            System.out.printf("MecaniQA API listening on port %d%n", PORT);
            System.out.printf("MySQL configured at %s:%d%n", DB_HOST, DB_PORT);
            System.out.printf("Redis configured at %s:%d%n", REDIS_HOST, REDIS_PORT);
            while (true) {
                handle(server.accept());
            }
        }
    }

    private static void handle(Socket socket) {
        try (socket;
             BufferedReader reader = new BufferedReader(
                     new InputStreamReader(socket.getInputStream(), StandardCharsets.US_ASCII));
             OutputStream output = socket.getOutputStream()) {
            String requestLine = reader.readLine();
            boolean healthRequest = requestLine != null && requestLine.startsWith("GET /health ");
            boolean mysqlUp = healthRequest && canConnect(DB_HOST, DB_PORT);
            boolean redisUp = healthRequest && canConnect(REDIS_HOST, REDIS_PORT);
            boolean healthy = healthRequest && mysqlUp && redisUp;

            byte[] body;
            String status;
            if (healthRequest) {
                status = healthy ? "200 OK" : "503 Service Unavailable";
                body = ("{\"status\":\"" + (healthy ? "UP" : "DOWN")
                        + "\",\"service\":\"mecaniqa-api\",\"mysql\":\""
                        + dependencyStatus(mysqlUp) + "\",\"redis\":\""
                        + dependencyStatus(redisUp) + "\"}").getBytes(StandardCharsets.UTF_8);
            } else {
                status = "404 Not Found";
                body = NOT_FOUND_RESPONSE;
            }

            String headers = "HTTP/1.1 " + status + "\r\n"
                    + "Content-Type: application/json; charset=utf-8\r\n"
                    + "Content-Length: " + body.length + "\r\n"
                    + "Connection: close\r\n\r\n";

            output.write(headers.getBytes(StandardCharsets.US_ASCII));
            output.write(body);
            output.flush();
        } catch (IOException exception) {
            System.err.println("Failed to process request: " + exception.getMessage());
        }
    }

    private static boolean canConnect(String host, int port) {
        try (Socket dependency = new Socket()) {
            dependency.connect(new InetSocketAddress(host, port), CONNECTION_TIMEOUT_MS);
            return true;
        } catch (IOException exception) {
            System.err.printf("Dependency unavailable at %s:%d: %s%n",
                    host, port, exception.getMessage());
            return false;
        }
    }

    private static String dependencyStatus(boolean available) {
        return available ? "UP" : "DOWN";
    }

    private static String environment(String name, String defaultValue) {
        String value = System.getenv(name);
        return value == null || value.isBlank() ? defaultValue : value;
    }

    private static int environmentPort(String name, int defaultValue) {
        String value = System.getenv(name);
        if (value == null || value.isBlank()) {
            return defaultValue;
        }
        try {
            return Integer.parseInt(value);
        } catch (NumberFormatException exception) {
            throw new IllegalArgumentException(name + " must be a valid port: " + value, exception);
        }
    }
}
