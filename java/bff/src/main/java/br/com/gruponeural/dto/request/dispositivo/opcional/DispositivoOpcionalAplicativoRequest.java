package br.com.gruponeural.dto.request.dispositivo.opcional;

import java.util.ArrayList;

import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

@Getter
@Setter
@NoArgsConstructor
public class DispositivoOpcionalAplicativoRequest {

    private String descricao;
    private String versaoExpo;
    private String versaoExpoRuntime;
    private String iosPacoteId;
    private String iosBuildId;
    private String iosVersao;
    private String androidPacoteId;
    private Integer androidBuildId;
    private String androidVersao;
    private String webUrlBase;
    private String proprietario;
    private ArrayList<String> listaPlatarforma;
    private ArrayList<String> listaEsquema;
    private String extra;

}
