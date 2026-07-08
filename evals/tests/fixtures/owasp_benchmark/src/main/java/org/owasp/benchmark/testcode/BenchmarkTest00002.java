package org.owasp.benchmark.testcode;

public class BenchmarkTest00002 {
    public void doPost() {
        String safe = "select * from users where id = ?";
        System.out.println(safe);
    }
}

