package br.com.gruponeural.infrastructure.restclient.cortex.sessao;

import org.eclipse.microprofile.rest.client.inject.RegisterRestClient;

import br.com.gruponeural.dto.request.dispositivo.DispositivoAtualizarRequest;
import br.com.gruponeural.dto.response.dispositivo.DispositivoAtualizarResponse;
import io.smallrye.mutiny.Uni;
import jakarta.ws.rs.Consumes;
import jakarta.ws.rs.POST;
import jakarta.ws.rs.Path;
import jakarta.ws.rs.Produces;
import jakarta.ws.rs.core.MediaType;

@RegisterRestClient(configKey = "cortex-sessao")
@Produces(MediaType.APPLICATION_JSON)
@Path("dispositivo/v1")
public interface SessaoDispositivoRestClient {

    @POST
    @Path("atualizar")
    @Consumes(MediaType.APPLICATION_JSON)
    Uni<DispositivoAtualizarResponse> atualizarDispositivo(DispositivoAtualizarRequest body);

}
