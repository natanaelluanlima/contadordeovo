package br.com.gruponeural.dto.request.dispositivo.obrigatorio;

import java.util.UUID;

import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

@Getter
@Setter
@NoArgsConstructor
public class DispositivoObrigatorioRequest {

    private UUID id;
    private String marca;
    private String fabricante;
    private String nomeModelo;
    private String idModelo;
    private String tipo;
    private Boolean emulador;
    private Integer memoriaRAMTotalMB;
    private String nomeDispositivo;
    private DispositivoObrigatorioAplicativoRequest aplicativo;
    private DispositivoObrigatorioSegurancaRequest seguranca;
    private DispositivoObrigatorioSistemaOperacionalRequest sistemaOperacional;

}
