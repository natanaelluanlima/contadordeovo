package br.com.gruponeural.core.helper;

public class RouteHelper {

    public static String mascararDadosSensiveis(String json) {
        if (json == null || json.isEmpty()) {
            return json;
        }

        try {
            // Regex para capturar valores de chaves sensíveis
            String regex = "(?i)\"(senha|password|token|secret|tokenAcesso)\"\\s*:\\s*\"[^\"]+\"";

            // Substitui o valor capturado por * mantendo a chave original ($1)
            return json.replaceAll(regex, "\"$1\":\"********\"");
        } catch (Exception e) {
            // Em caso de erro do regex, retorna uma mensagem segura
            return "[ERRO AO MASCARAR DADOS SENSÍVEIS]";
        }
    }

}
