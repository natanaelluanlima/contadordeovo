package br.com.gruponeural.application.resource.screen.centralcontrole.usuario;

import br.com.gruponeural.dto.usuario.UsuarioAlterarRequest;
import br.com.gruponeural.dto.usuario.UsuarioAlterarResponse;
import br.com.gruponeural.dto.usuario.UsuarioCadastrarRequest;
import br.com.gruponeural.dto.usuario.UsuarioCadastrarResponse;
import br.com.gruponeural.dto.usuario.UsuarioExcluirResponse;
import br.com.gruponeural.dto.usuario.UsuarioListarResponse;
import br.com.gruponeural.dto.usuario.UsuarioObterResponse;
import io.smallrye.mutiny.Uni;

public interface UsuarioCentralControleScreenResource {

    Uni<UsuarioListarResponse> listar(Integer pageNumber, Integer pageSize);

    Uni<UsuarioCadastrarResponse> cadastrar(UsuarioCadastrarRequest request);

    Uni<UsuarioObterResponse> obter(String id);

    Uni<UsuarioAlterarResponse> alterar(String id, UsuarioAlterarRequest request);

    Uni<UsuarioExcluirResponse> excluir(String id);
}
