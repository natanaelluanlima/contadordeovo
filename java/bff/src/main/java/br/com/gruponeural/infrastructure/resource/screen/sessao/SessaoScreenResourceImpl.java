package br.com.gruponeural.infrastructure.resource.screen.sessao;

import org.eclipse.microprofile.openapi.annotations.parameters.Parameter;
import org.eclipse.microprofile.openapi.annotations.tags.Tag;

import br.com.gruponeural.application.resource.screen.sessao.SessaoScreenResource;
import br.com.gruponeural.application.usecase.screen.sessao.SessaoScreenEntrarUseCase;
import br.com.gruponeural.application.usecase.screen.sessao.SessaoScreenRenovarUseCase;
import br.com.gruponeural.application.usecase.screen.sessao.SessaoScreenSairUseCase;
import br.com.gruponeural.core.log.LogUtil;
import br.com.gruponeural.dto.request.sessao.SessaoEntrarRequest;
import br.com.gruponeural.dto.request.sessao.SessaoRenovarRequest;
import br.com.gruponeural.dto.request.sessao.SessaoSairRequest;
import br.com.gruponeural.dto.response.sessao.SessaoEntrarResponse;
import br.com.gruponeural.dto.response.sessao.SessaoRenovarResponse;
import br.com.gruponeural.dto.response.sessao.SessaoSairResponse;
import io.smallrye.mutiny.Uni;
import jakarta.enterprise.context.ApplicationScoped;
import jakarta.inject.Inject;
import jakarta.ws.rs.Consumes;
import jakarta.ws.rs.POST;
import jakarta.ws.rs.Path;
import jakarta.ws.rs.Produces;
import jakarta.ws.rs.core.MediaType;

@Path("v1/screen/sessao")
@Produces(MediaType.APPLICATION_JSON)
@Tag(name = "Sessão (tela)", description = "Login, renovação e encerramento de sessão via Cortex Sessão")
@ApplicationScoped
public class SessaoScreenResourceImpl
    implements SessaoScreenResource {

    @Inject
    SessaoScreenEntrarUseCase sessaoScreenEntrarUseCase;

    @Inject
    SessaoScreenRenovarUseCase sessaoScreenRenovarUseCase;

    @Inject
    SessaoScreenSairUseCase sessaoScreenSairUseCase;

    @POST
    @Path("entrar")
    @Consumes(MediaType.APPLICATION_JSON)
    @Override
    public Uni<SessaoEntrarResponse> entrar(
        @Parameter(description = "Credenciais e dispositivo", required = true)
        SessaoEntrarRequest request) {

        return sessaoScreenEntrarUseCase
            .entrar(request)
            .onItem()
            .invoke(response ->
                LogUtil
                    .trace()
                    .setClass(this.getClass())
                    .setMethodName("entrar")
                    .setValuesName("response")
                    .setValues(response)
                    .build())
            .onFailure()
            .invoke(throwable ->
                LogUtil
                    .error()
                    .setClass(this.getClass())
                    .setMethodName("entrar")
                    .setThrowable(throwable)
                    .build());

    }

    @POST
    @Path("renovar")
    @Consumes(MediaType.APPLICATION_JSON)
    @Override
    public Uni<SessaoRenovarResponse> renovar(
        @Parameter(description = "Dispositivo e sessão atuais", required = true)
        SessaoRenovarRequest request) {

        return sessaoScreenRenovarUseCase
            .renovar(request)
            .onItem()
            .invoke(response ->
                LogUtil
                    .trace()
                    .setClass(this.getClass())
                    .setMethodName("renovar")
                    .setValuesName("response")
                    .setValues(response)
                    .build())
            .onFailure()
            .invoke(throwable ->
                LogUtil
                    .error()
                    .setClass(this.getClass())
                    .setMethodName("renovar")
                    .setThrowable(throwable)
                    .build());

    }

    @POST
    @Path("sair")
    @Consumes(MediaType.APPLICATION_JSON)
    @Override
    public Uni<SessaoSairResponse> sair(
        @Parameter(description = "Dispositivo e sessão a encerrar", required = true)
        SessaoSairRequest request) {

        return sessaoScreenSairUseCase
            .sair(request)
            .onItem()
            .invoke(response ->
                LogUtil
                    .trace()
                    .setClass(this.getClass())
                    .setMethodName("sair")
                    .setValuesName("response")
                    .setValues(response)
                    .build())
            .onFailure()
            .invoke(throwable ->
                LogUtil
                    .error()
                    .setClass(this.getClass())
                    .setMethodName("sair")
                    .setThrowable(throwable)
                    .build());

    }

}
