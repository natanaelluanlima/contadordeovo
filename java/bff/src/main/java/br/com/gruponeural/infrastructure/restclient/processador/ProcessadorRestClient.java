package br.com.gruponeural.infrastructure.restclient.processador;

import java.util.Map;

import org.eclipse.microprofile.rest.client.inject.RegisterRestClient;

import jakarta.ws.rs.Consumes;
import jakarta.ws.rs.GET;
import jakarta.ws.rs.POST;
import jakarta.ws.rs.Path;
import jakarta.ws.rs.Produces;
import jakarta.ws.rs.core.MediaType;
import org.jboss.resteasy.reactive.RestForm;
import org.jboss.resteasy.reactive.multipart.FileUpload;

import io.smallrye.mutiny.Uni;

@RegisterRestClient(configKey = "egg-processador")
@Path("/gruponeural/egg/processador")
@Produces(MediaType.APPLICATION_JSON)
public interface ProcessadorRestClient {

    @GET
    @Path("/health")
    Uni<Map<String, Object>> health();

    @GET
    @Path("/v1/session/status")
    Uni<Map<String, Object>> status();

    @POST
    @Path("/v1/session/start")
    @Consumes(MediaType.APPLICATION_JSON)
    Uni<Map<String, Object>> start(Map<String, Object> body);

    @POST
    @Path("/v1/session/stop")
    Uni<Map<String, Object>> stop();

    @POST
    @Path("/v1/session/frame")
    @Consumes(MediaType.MULTIPART_FORM_DATA)
    Uni<Map<String, Object>> frame(@RestForm("file") FileUpload file);

    @POST
    @Path("/v1/session/frame-b64")
    @Consumes(MediaType.APPLICATION_JSON)
    Uni<Map<String, Object>> frameB64(Map<String, Object> body);
}
