package br.com.gruponeural.infrastructure.resource.screen.contagem;

import java.util.Map;

import org.eclipse.microprofile.rest.client.inject.RestClient;
import org.jboss.resteasy.reactive.RestForm;
import org.jboss.resteasy.reactive.multipart.FileUpload;

import br.com.gruponeural.application.resource.screen.contagem.ContagemScreenResource;
import br.com.gruponeural.infrastructure.restclient.processador.ProcessadorRestClient;
import io.smallrye.mutiny.Uni;
import jakarta.enterprise.context.ApplicationScoped;
import jakarta.ws.rs.Consumes;
import jakarta.ws.rs.GET;
import jakarta.ws.rs.POST;
import jakarta.ws.rs.Path;
import jakarta.ws.rs.Produces;
import jakarta.ws.rs.core.MediaType;
import org.eclipse.microprofile.openapi.annotations.tags.Tag;

@Path("v1/screen/contagem")
@Produces(MediaType.APPLICATION_JSON)
@Tag(name = "Contagem (tela)", description = "Contagem de ovos via processador Python")
@ApplicationScoped
public class ContagemScreenResourceImpl implements ContagemScreenResource {

    @RestClient
    ProcessadorRestClient processadorRestClient;

    @GET
    @Path("status")
    @Override
    public Uni<Map<String, Object>> status() {
        return processadorRestClient.status();
    }

    @POST
    @Path("iniciar")
    @Consumes(MediaType.APPLICATION_JSON)
    @Override
    public Uni<Map<String, Object>> iniciar(Map<String, Object> body) {
        return processadorRestClient.start(body != null ? body : Map.of());
    }

    @POST
    @Path("parar")
    @Override
    public Uni<Map<String, Object>> parar() {
        return processadorRestClient.stop();
    }

    @POST
    @Path("frame")
    @Consumes(MediaType.MULTIPART_FORM_DATA)
    @Override
    public Uni<Map<String, Object>> frame(@RestForm("file") FileUpload file) {
        return processadorRestClient.frame(file);
    }

    @POST
    @Path("frame-b64")
    @Consumes(MediaType.APPLICATION_JSON)
    @Override
    public Uni<Map<String, Object>> frameB64(Map<String, Object> body) {
        return processadorRestClient.frameB64(body != null ? body : Map.of());
    }
}
