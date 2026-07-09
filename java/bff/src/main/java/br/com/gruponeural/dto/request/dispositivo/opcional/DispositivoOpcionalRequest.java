package br.com.gruponeural.dto.request.dispositivo.opcional;

import java.util.ArrayList;

import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

@Getter
@Setter
@NoArgsConstructor
public class DispositivoOpcionalRequest {

    private ArrayList<String> listaArquiteruraCpu;
    private ArrayList<String> listaRecurso;
    private DispositivoOpcionalAplicativoRequest aplicativo;
    private DispositivoOpcionalSistemaOperacionalRequest sistemaOperacional;

}
