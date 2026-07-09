package br.com.gruponeural.infrastructure.restclient.cortex.sessao;

import org.eclipse.microprofile.rest.client.inject.RegisterRestClient;

import br.com.gruponeural.dto.request.sessao.SessaoEntrarCortexRequest;
import br.com.gruponeural.dto.request.sessao.SessaoRenovarRequest;
import br.com.gruponeural.dto.request.sessao.SessaoSairRequest;
import br.com.gruponeural.dto.response.sessao.SessaoEntrarResponse;
import br.com.gruponeural.dto.response.sessao.SessaoRenovarResponse;
import br.com.gruponeural.dto.response.sessao.SessaoSairResponse;
import io.smallrye.mutiny.Uni;
import jakarta.ws.rs.Consumes;
import jakarta.ws.rs.POST;
import jakarta.ws.rs.Path;
import jakarta.ws.rs.Produces;
import jakarta.ws.rs.core.MediaType;

@RegisterRestClient(configKey = "cortex-sessao")
@Produces(MediaType.APPLICATION_JSON)
@Path("v1")
public interface SessaoSessaoRestClient {

    @POST
    @Path("entrar")
    @Consumes(MediaType.APPLICATION_JSON)
    Uni<SessaoEntrarResponse> entrar(SessaoEntrarCortexRequest body);

    @POST
    @Path("renovar")
    @Consumes(MediaType.APPLICATION_JSON)
    Uni<SessaoRenovarResponse> renovar(SessaoRenovarRequest body);

    @POST
    @Path("sair")
    @Consumes(MediaType.APPLICATION_JSON)
    Uni<SessaoSairResponse> sair(SessaoSairRequest body);

}
