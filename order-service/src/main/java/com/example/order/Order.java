package com.example.order;

public class Order {

    private Long id;
    private String productName;
    private Integer quantity;
    private Integer price;
    private String status;

    public Order() {
    }

    public Order(Long id, String productName, Integer quantity, Integer price, String status) {
        this.id = id;
        this.productName = productName;
        this.quantity = quantity;
        this.price = price;
        this.status = status;
    }

    public Long getId() {
        return id;
    }

    public void setId(Long id) {
        this.id = id;
    }

    public String getProductName() {
        return productName;
    }

    public void setProductName(String productName) {
        this.productName = productName;
    }

    public Integer getQuantity() {
        return quantity;
    }

    public void setQuantity(Integer quantity) {
        this.quantity = quantity;
    }

    public Integer getPrice() {
        return price;
    }

    public void setPrice(Integer price) {
        this.price = price;
    }

    public String getStatus() {
        return status;
    }

    public void setStatus(String status) {
        this.status = status;
    }
}
