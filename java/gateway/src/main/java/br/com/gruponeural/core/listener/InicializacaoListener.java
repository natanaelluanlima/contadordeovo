package br.com.gruponeural.core.listener;

import org.eclipse.microprofile.config.inject.ConfigProperty;

import io.quarkus.logging.Log;
import io.quarkus.runtime.StartupEvent;
import jakarta.enterprise.context.ApplicationScoped;
import jakarta.enterprise.event.Observes;

@ApplicationScoped
public class InicializacaoListener {

    @ConfigProperty(name = "quarkus.application.name", defaultValue = "")
    String nomeAplicacao;

    @ConfigProperty(name = "quarkus.http.root-path", defaultValue = "")
    String rotaAplicacao;

    @ConfigProperty(name = "quarkus.http.port", defaultValue = "")
    String portaAplicacao;

    void onStartup(@Observes StartupEvent event) {

        Log.info("Aplicação [" + nomeAplicacao + "] iniciada na rota [" + rotaAplicacao + "] e porta [" + portaAplicacao + "].");

    }

}
