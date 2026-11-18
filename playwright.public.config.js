const {defineConfig}=require('@playwright/test');
module.exports=defineConfig({testDir:'./tests/public',outputDir:'test-results/public',workers:1,timeout:300000,
  reporter:[['list'],['html',{open:'never',outputFolder:'playwright-report/public'}]],
  use:{baseURL:process.env.PUBLIC_DEMO_URL || 'https://expensas-house-griselda-blanco.vercel.app',trace:'retain-on-failure',screenshot:'only-on-failure'}});
