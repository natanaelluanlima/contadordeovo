package br.com.gruponeural.dto.cliente;

import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

@Getter
@Setter
@NoArgsConstructor
public class ClienteAlterarRequest {

    private String id;
    private String nome;
}

