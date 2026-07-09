package br.com.gruponeural.health;

import java.time.LocalDateTime;

import org.eclipse.microprofile.config.inject.ConfigProperty;
import org.eclipse.microprofile.health.HealthCheck;
import org.eclipse.microprofile.health.HealthCheckResponse;
import org.eclipse.microprofile.health.Liveness;

import jakarta.enterprise.context.ApplicationScoped;

@Liveness
@ApplicationScoped
public class HealthCheckImpl
    implements HealthCheck {

    @ConfigProperty(name = "app.version", defaultValue = "unknown")
    String version;

    @Override
    public HealthCheckResponse call() {
        return HealthCheckResponse
            .named("Cortex - Gateway Health Check")
            .up()
            .withData("timestamp", LocalDateTime.now().toString())
            .withData("version", version)
            .build();
    }
}