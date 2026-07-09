package br.com.gruponeural.application.resource.screen.contagem;

import java.util.Map;

import org.jboss.resteasy.reactive.multipart.FileUpload;

import io.smallrye.mutiny.Uni;

public interface ContagemScreenResource {

    Uni<Map<String, Object>> status();

    Uni<Map<String, Object>> iniciar(Map<String, Object> body);

    Uni<Map<String, Object>> parar();

    Uni<Map<String, Object>> frame(FileUpload file);

    Uni<Map<String, Object>> frameB64(Map<String, Object> body);
}
