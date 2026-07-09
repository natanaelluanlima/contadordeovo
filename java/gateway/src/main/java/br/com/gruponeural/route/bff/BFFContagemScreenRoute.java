package br.com.gruponeural.route.bff;

import br.com.gruponeural.core.route.Route;
import br.com.gruponeural.core.route.RoutePath;
import jakarta.enterprise.context.ApplicationScoped;

@ApplicationScoped
public class BFFContagemScreenRoute extends Route {

    @Override
    public void configure() {
        configurarServico("contagem");
        configurarUrlDestino("http://localhost:9001/gruponeural/egg/bff");
        // Primeiro frame pode carregar YOLO (dezenas de segundos em CPU).
        configurarHttpResponseTimeoutMs(180_000);

        adicionarRota(new RoutePath("screen/status", "v1/screen/contagem/status", "GET", false));
        adicionarRota(new RoutePath("screen/iniciar", "v1/screen/contagem/iniciar", "POST", false));
        adicionarRota(new RoutePath("screen/parar", "v1/screen/contagem/parar", "POST", false));
        adicionarRota(new RoutePath("screen/frame", "v1/screen/contagem/frame", "POST", false, false, true));
        adicionarRota(new RoutePath("screen/frame-b64", "v1/screen/contagem/frame-b64", "POST", false));

        super.configure();
    }
}
