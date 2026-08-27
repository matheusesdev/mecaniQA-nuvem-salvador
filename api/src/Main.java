import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;
import java.io.OutputStream;
import java.net.ServerSocket;
import java.net.Socket;
import java.nio.charset.StandardCharsets;

public final class Main {
    private static final int PORT = 8080;
    private static final byte[] HEALTH_RESPONSE =
            "{\"status\":\"UP\",\"service\":\"mecaniqa-api\"}".getBytes(StandardCharsets.UTF_8);
    private static final byte[] NOT_FOUND_RESPONSE =
            "{\"status\":\"NOT_FOUND\"}".getBytes(StandardCharsets.UTF_8);

    private Main() {
    }

    public static void main(String[] args) throws IOException {
        try (ServerSocket server = new ServerSocket(PORT)) {
            System.out.printf("MecaniQA API listening on port %d%n", PORT);
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
            byte[] body = healthRequest ? HEALTH_RESPONSE : NOT_FOUND_RESPONSE;
            String status = healthRequest ? "200 OK" : "404 Not Found";

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
}
