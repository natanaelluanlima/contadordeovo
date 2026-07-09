package br.com.gruponeural.infrastructure.resource.screen.localizacao;

import java.util.List;

import org.eclipse.microprofile.openapi.annotations.parameters.Parameter;
import org.eclipse.microprofile.openapi.annotations.tags.Tag;

import br.com.gruponeural.application.resource.screen.localizacao.LocalizacaoScreenResource;
import br.com.gruponeural.application.usecase.screen.localizacao.LocalizacaoScreenAlterarBairroUseCase;
import br.com.gruponeural.application.usecase.screen.localizacao.LocalizacaoScreenCadastrarBairroUseCase;
import br.com.gruponeural.application.usecase.screen.localizacao.LocalizacaoScreenExcluirBairroUseCase;
import br.com.gruponeural.application.usecase.screen.localizacao.LocalizacaoScreenListarBairrosUseCase;
import br.com.gruponeural.application.usecase.screen.localizacao.LocalizacaoScreenListarCidadesUseCase;
import br.com.gruponeural.application.usecase.screen.localizacao.LocalizacaoScreenListarEstadosUseCase;
import br.com.gruponeural.application.usecase.screen.localizacao.LocalizacaoScreenObterBairroUseCase;
import br.com.gruponeural.core.log.LogUtil;
import br.com.gruponeural.dto.localizacao.BairroAlterarRequest;
import br.com.gruponeural.dto.localizacao.BairroCadastrarRequest;
import br.com.gruponeural.dto.localizacao.BairroExcluirResponse;
import br.com.gruponeural.dto.localizacao.BairroObterResponse;
import br.com.gruponeural.dto.localizacao.LocalizacaoItemDTO;
import io.smallrye.mutiny.Uni;
import jakarta.enterprise.context.ApplicationScoped;
import jakarta.inject.Inject;
import jakarta.ws.rs.Consumes;
import jakarta.ws.rs.DELETE;
import jakarta.ws.rs.GET;
import jakarta.ws.rs.POST;
import jakarta.ws.rs.PUT;
import jakarta.ws.rs.Path;
import jakarta.ws.rs.PathParam;
import jakarta.ws.rs.Produces;
import jakarta.ws.rs.QueryParam;
import jakarta.ws.rs.core.MediaType;

@Path("v1/screen/localizacao")
@Produces(MediaType.APPLICATION_JSON)
@Tag(name = "Localizacao (tela)", description = "Operacoes da tela de localizacao via BFF")
@ApplicationScoped
public class LocalizacaoScreenResourceImpl implements LocalizacaoScreenResource {

    @Inject
    LocalizacaoScreenListarEstadosUseCase localizacaoScreenListarEstadosUseCase;

    @Inject
    LocalizacaoScreenListarCidadesUseCase localizacaoScreenListarCidadesUseCase;

    @Inject
    LocalizacaoScreenListarBairrosUseCase localizacaoScreenListarBairrosUseCase;

    @Inject
    LocalizacaoScreenCadastrarBairroUseCase localizacaoScreenCadastrarBairroUseCase;

    @Inject
    LocalizacaoScreenObterBairroUseCase localizacaoScreenObterBairroUseCase;

    @Inject
    LocalizacaoScreenAlterarBairroUseCase localizacaoScreenAlterarBairroUseCase;

    @Inject
    LocalizacaoScreenExcluirBairroUseCase localizacaoScreenExcluirBairroUseCase;

    @GET
    @Path("estado/listar")
    @Override
    public Uni<List<LocalizacaoItemDTO>> listarEstados() {
        return localizacaoScreenListarEstadosUseCase
            .listar()
            .onItem()
            .invoke(response -> LogUtil
                .trace()
                .setClass(this.getClass())
                .setMethodName("listarEstados")
                .setValuesName("response")
                .setValues(response)
                .build())
            .onFailure()
            .invoke(throwable -> LogUtil
                .error()
                .setClass(this.getClass())
                .setMethodName("listarEstados")
                .setThrowable(throwable)
                .build());
    }

    @GET
    @Path("cidade/listar")
    @Override
    public Uni<List<LocalizacaoItemDTO>> listarCidades(
        @Parameter(description = "Identificador do estado", required = true)
        @QueryParam("idEstado") String idEstado) {

        return localizacaoScreenListarCidadesUseCase
            .listar(idEstado)
            .onItem()
            .invoke(response -> LogUtil
                .trace()
                .setClass(this.getClass())
                .setMethodName("listarCidades")
                .setValuesName("response")
                .setValues(response)
                .build())
            .onFailure()
            .invoke(throwable -> LogUtil
                .error()
                .setClass(this.getClass())
                .setMethodName("listarCidades")
                .setThrowable(throwable)
                .build());
    }

    @GET
    @Path("bairro/listar")
    @Override
    public Uni<List<LocalizacaoItemDTO>> listarBairros(
        @Parameter(description = "Identificador da cidade", required = true)
        @QueryParam("idCidade") String idCidade) {

        return localizacaoScreenListarBairrosUseCase
            .listar(idCidade)
            .onItem()
            .invoke(response -> LogUtil
                .trace()
                .setClass(this.getClass())
                .setMethodName("listarBairros")
                .setValuesName("response")
                .setValues(response)
                .build())
            .onFailure()
            .invoke(throwable -> LogUtil
                .error()
                .setClass(this.getClass())
                .setMethodName("listarBairros")
                .setThrowable(throwable)
                .build());
    }

    @POST
    @Path("bairro/cadastrar")
    @Consumes(MediaType.APPLICATION_JSON)
    @Override
    public Uni<LocalizacaoItemDTO> cadastrarBairro(
        @Parameter(description = "Identificador da cidade", required = true)
        @QueryParam("idCidade") String idCidade,
        @Parameter(description = "Dados do novo bairro", required = true)
        BairroCadastrarRequest request) {

        return localizacaoScreenCadastrarBairroUseCase
            .cadastrar(idCidade, request)
            .onItem()
            .invoke(response -> LogUtil
                .trace()
                .setClass(this.getClass())
                .setMethodName("cadastrarBairro")
                .setValuesName("response")
                .setValues(response)
                .build())
            .onFailure()
            .invoke(throwable -> LogUtil
                .error()
                .setClass(this.getClass())
                .setMethodName("cadastrarBairro")
                .setThrowable(throwable)
                .build());
    }

    @GET
    @Path("bairro/obter/{id}")
    @Override
    public Uni<BairroObterResponse> obterBairro(
        @Parameter(description = "Identificador do bairro", required = true)
        @PathParam("id") String id) {

        return localizacaoScreenObterBairroUseCase
            .obter(id)
            .onItem()
            .invoke(response -> LogUtil
                .trace()
                .setClass(this.getClass())
                .setMethodName("obterBairro")
                .setValuesName("response")
                .setValues(response)
                .build())
            .onFailure()
            .invoke(throwable -> LogUtil
                .error()
                .setClass(this.getClass())
                .setMethodName("obterBairro")
                .setThrowable(throwable)
                .build());
    }

    @PUT
    @Path("bairro/alterar/{id}")
    @Consumes(MediaType.APPLICATION_JSON)
    @Override
    public Uni<LocalizacaoItemDTO> alterarBairro(
        @Parameter(description = "Identificador do bairro", required = true)
        @PathParam("id") String id,
        @Parameter(description = "Dados para alteracao", required = true)
        BairroAlterarRequest request) {

        return localizacaoScreenAlterarBairroUseCase
            .alterar(id, request)
            .onItem()
            .invoke(response -> LogUtil
                .trace()
                .setClass(this.getClass())
                .setMethodName("alterarBairro")
                .setValuesName("response")
                .setValues(response)
                .build())
            .onFailure()
            .invoke(throwable -> LogUtil
                .error()
                .setClass(this.getClass())
                .setMethodName("alterarBairro")
                .setThrowable(throwable)
                .build());
    }

    @DELETE
    @Path("bairro/excluir/{id}")
    @Override
    public Uni<BairroExcluirResponse> excluirBairro(
        @Parameter(description = "Identificador do bairro", required = true)
        @PathParam("id") String id) {

        return localizacaoScreenExcluirBairroUseCase
            .excluir(id)
            .onItem()
            .invoke(response -> LogUtil
                .trace()
                .setClass(this.getClass())
                .setMethodName("excluirBairro")
                .setValuesName("response")
                .setValues(response)
                .build())
            .onFailure()
            .invoke(throwable -> LogUtil
                .error()
                .setClass(this.getClass())
                .setMethodName("excluirBairro")
                .setThrowable(throwable)
                .build());
    }
}
