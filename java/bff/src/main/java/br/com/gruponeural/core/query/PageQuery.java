package br.com.gruponeural.core.query;

import lombok.Getter;
import lombok.Setter;

@Getter
@Setter
public class PageQuery {

    private Integer pageNumber;
    private Long totalItems;
    private Integer firstResult;
    private Integer maxResults;

}
