package br.com.gruponeural.core.builder;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import br.com.gruponeural.core.builder.enumerator.SQLOperadorEnum;
import br.com.gruponeural.core.builder.enumerator.SQLOrdenacaoEnum;
import br.com.gruponeural.core.util.IntegerUtil;
import br.com.gruponeural.core.log.LogUtil;
import br.com.gruponeural.core.util.StringUtil;

public class SQLBuilder {

    private final String PREFIXO_PARAMETRO_CAMPO = "PARAMETRO_CAMPO_";
    private final String PREFIXO_PARAMETRO_WHERE = "PARAMETRO_WHERE_";

    private List<String> listaCampo = new ArrayList<String>();
    private Map<String, Object> listaCampoParametro = new HashMap<String, Object>();
    private List<String> listaWhere = new ArrayList<String>();
    private Map<String, Object> listaWhereParametro = new HashMap<String, Object>();
    private List<String> listaOrderBy = new ArrayList<String>();
    private Integer limite = IntegerUtil.zero();

    public void add(String campoNome, Object campoValor) {

        String sql = campoNome + " = :" + PREFIXO_PARAMETRO_CAMPO + campoNome;

        LogUtil
                .info()
                .setClass(this.getClass())
                .setMethodName("add")
                .setValuesName("campoNome", "campoValor", "sql")
                .setValues(campoNome, campoValor, sql)
                .build();

        this.listaCampo.add(sql);
        this.listaCampoParametro.put(PREFIXO_PARAMETRO_CAMPO + campoNome, campoValor);

    }

    public void addWhere(String campoNome, SQLOperadorEnum operador, Object campoValor) {

        String sql = campoNome + " " + operador.getOperador() + " :" + PREFIXO_PARAMETRO_WHERE + campoNome;

        LogUtil
                .info()
                .setClass(this.getClass())
                .setMethodName("addWhere")
                .setValuesName("campoNome", "operador", "campoValor", "sql")
                .setValues(campoNome, operador, campoValor, sql)
                .build();

        this.listaWhere.add(sql);
        this.listaWhereParametro.put(PREFIXO_PARAMETRO_WHERE + campoNome, campoValor);

    }

    public void addWhereNull(String campoNome) {

        String sql = campoNome + " " + SQLOperadorEnum.NULO.getOperador();

        LogUtil
                .info()
                .setClass(this.getClass())
                .setMethodName("addWhereNull")
                .setValuesName("campoNome", "sql")
                .setValues(campoNome, sql)
                .build();

        this.listaWhere.add(sql);

    }

    public void addOrder(String campoNome, SQLOrdenacaoEnum ordenacao) {

        String sql = campoNome + " " + ordenacao.getSentidoOrdenacao();

        LogUtil
                .info()
                .setClass(this.getClass())
                .setMethodName("addOrder")
                .setValuesName("campoNome", "ordenacao", "sql")
                .setValues(campoNome, ordenacao, sql)
                .build();

        this.listaOrderBy.add(sql);

    }

    public void addLimit(Integer quantidade) {

        LogUtil
                .info()
                .setClass(this.getClass())
                .setMethodName("addLimit")
                .setValuesName("quantidade")
                .setValues(quantidade)
                .build();

        this.limite = quantidade;

    }

    private String obterCampos() {

        StringBuilder camposBuilder = new StringBuilder();

        this.listaCampo.forEach(sql -> {

            if (camposBuilder.length() > 0) {

                camposBuilder.append(", ");

            }

            camposBuilder.append(sql);

        });

        LogUtil
                .info()
                .setClass(this.getClass())
                .setMethodName("obterCampos")
                .setValuesName("campos")
                .setValues(camposBuilder.toString())
                .build();

        return camposBuilder.toString();

    }

    private String obterWhere() {

        StringBuilder whereBuilder = new StringBuilder();

        this.listaWhere.forEach(sql -> {

            if (whereBuilder.length() > 0) {

                whereBuilder.append(" and ");

            }

            whereBuilder.append(sql);

        });

        LogUtil
                .info()
                .setClass(this.getClass())
                .setMethodName("obterWhere")
                .setValuesName("where")
                .setValues(whereBuilder.toString())
                .build();

        return whereBuilder.toString();

    }

    private String obterOrderBy() {

        StringBuilder orderByBuilder = new StringBuilder();

        this.listaOrderBy.forEach(sql -> {

            if (orderByBuilder.length() > 0) {

                orderByBuilder.append(", ");

            }

            orderByBuilder.append(sql);

        });

        LogUtil
                .info()
                .setClass(this.getClass())
                .setMethodName("obterOrderBy")
                .setValuesName("orderBy")
                .setValues(orderByBuilder.toString())
                .build();

        return orderByBuilder.toString();

    }

    private String obterLimit() {

        String limit = StringUtil.empty();

        if (this.limite > IntegerUtil.zero()) {

            limit = " limit " + this.limite;

        }

        LogUtil
                .info()
                .setClass(this.getClass())
                .setMethodName("obterLimit")
                .setValuesName("limit")
                .setValues(limit)
                .build();

        return limit;

    }

    public String query() {

        LogUtil
                .info()
                .setClass(this.getClass())
                .setMethodName("query")
                .build();

        String campos = obterCampos();
        String where = obterWhere();
        String orderBy = obterOrderBy();
        String limit = obterLimit();

        LogUtil
                .info()
                .setClass(this.getClass())
                .setMethodName("query")
                .setValuesName("campos", "where", "orderBy", "limit")
                .setValues(campos, where, orderBy, limit)
                .build();

        String sql = campos;

        if (!StringUtil.isEmpty(campos) && !StringUtil.isEmpty(where)) {

            sql = sql.trim() + " where " + where;

        } else {

            sql = sql.trim() + " " + where;

        }

        if (!StringUtil.isEmpty(orderBy)) {

            sql = sql.trim() + " order by " + orderBy;

        }

        if (!StringUtil.isEmpty(limit)) {

            sql = sql.trim() + limit;

        }

        LogUtil
                .info()
                .setClass(this.getClass())
                .setMethodName("query")
                .setValuesName("sql")
                .setValues(sql)
                .build();

        return sql;

    }

    public Map<String, Object> params() {

        LogUtil
                .info()
                .setClass(this.getClass())
                .setMethodName("params")
                .setValuesName("listaCampoParametro", "listaWhereParametro")
                .setValues(this.listaCampoParametro, this.listaWhereParametro)
                .build();

        Map<String, Object> listaParametro = new HashMap<String, Object>();

        listaParametro.putAll(this.listaCampoParametro);
        listaParametro.putAll(this.listaWhereParametro);

        LogUtil
                .info()
                .setClass(this.getClass())
                .setMethodName("params")
                .setValuesName("listaParametro")
                .setValues(listaParametro)
                .build();

        return listaParametro;

    }

}
