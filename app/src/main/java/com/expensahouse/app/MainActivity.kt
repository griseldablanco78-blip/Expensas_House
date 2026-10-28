package com.expensahouse.app

import android.app.Activity
import android.content.Intent
import android.os.Bundle
import android.speech.RecognizerIntent
import android.widget.Toast
import androidx.activity.ComponentActivity
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.compose.setContent
import androidx.activity.result.contract.ActivityResultContracts
import androidx.lifecycle.ViewModelProvider
import com.expensahouse.app.core.auth.AuthSession
import com.expensahouse.app.data.remote.ExpensaApiClient
import com.expensahouse.app.ui.features.auth.ChangePasswordDialog
import com.expensahouse.app.ui.features.auth.AccountGate
import kotlinx.coroutines.launch
import androidx.compose.foundation.background
import androidx.compose.foundation.horizontalScroll
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.LazyRow
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.LocalUriHandler
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.expensahouse.app.domain.model.*
import com.expensahouse.app.ui.theme.*
import com.expensahouse.app.ui.viewmodel.*
import com.expensahouse.app.ui.components.VoiceOutlinedTextField
import com.expensahouse.app.ui.features.offers.ConnectedOfferSearch
import com.expensahouse.app.ui.features.chat.ConnectedChatDialog
import com.expensahouse.app.ui.features.receipts.ConnectedReceiptDialog


private val categories = listOf("Comestibles", "Limpieza", "Carnicería", "Verdulería", "Hogar")

class MainActivity : ComponentActivity() {


    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent {
            AccountGate(beforeSessionChange = { viewModelStore.clear() }) {
                val model = ViewModelProvider(this)[ExpensaViewModel::class.java]
                ExpensaHouseApp(model)
            }
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
private fun ExpensaHouseApp(viewModel: ExpensaViewModel) {
    val account by AuthSession.user.collectAsState()
    val canEdit = AuthSession.canEdit
    val inventoryOnly = account?.role == "inventory_viewer"
    val sessionScope = rememberCoroutineScope()
    var changePassword by remember { mutableStateOf(false) }
    if (changePassword) ChangePasswordDialog { changePassword = false }
    var selectedTab by rememberSaveable { mutableIntStateOf(if (inventoryOnly) 1 else 0) }
    var showAddDialog by remember { mutableStateOf(false) }
    var showEditDialog by remember { mutableStateOf<StockItem?>(null) }
    var showOpenPicker by remember { mutableStateOf(false) }
    var showAddOfferDialog by remember { mutableStateOf(false) }
    var showAddShoppingDialog by remember { mutableStateOf(false) }
    var showBudgetDialog by remember { mutableStateOf(false) }
    var showExpenseDialog by remember { mutableStateOf(false) }
    var showBotiChat by remember { mutableStateOf(false) }
    var showScanTicketDialog by rememberSaveable { mutableStateOf(false) }
    var offerQuery by remember { mutableStateOf("") }

    val stock by viewModel.stock.collectAsStateWithLifecycle()
    val shopping by viewModel.shopping.collectAsStateWithLifecycle()
    val savedOffers by viewModel.savedOffers.collectAsStateWithLifecycle()
    val userPrefs by viewModel.userPrefs.collectAsStateWithLifecycle(UserPrefs())
    val expenses by viewModel.expenses.collectAsStateWithLifecycle()
    val context = LocalContext.current

    LaunchedEffect(viewModel) {
        viewModel.syncMessages.collect { message ->
            Toast.makeText(context, message, Toast.LENGTH_LONG).show()
        }
    }

    ExpensaHouseTheme {
        Scaffold(
            containerColor = Canvas,
            topBar = {
                CenterAlignedTopAppBar(
                    title = {
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            Icon(Icons.Filled.Home, null, tint = Leaf, modifier = Modifier.size(24.dp))
                            Spacer(Modifier.width(12.dp))
                            Text("EXPENSA HOUSE", style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.Black, color = Ink, letterSpacing = 1.5.sp)
                        }
                    },
                    actions = {
                        TextButton(onClick = { changePassword = true }) { Text("Clave") }
                        TextButton(onClick = {
                            sessionScope.launch {
                                try { ExpensaApiClient.service.logout() } finally { AuthSession.clear() }
                            }
                        }) { Text("Salir") }
                        if (!inventoryOnly) IconButton(onClick = { showBotiChat = true }) {
                            Icon(Icons.Filled.AutoAwesome, "Boti House Chatbot", tint = Gold)
                        }
                        IconButton(onClick = { viewModel.onEvent(ExpensaEvent.RefreshData) }) {
                            Icon(Icons.Filled.Sync, "Sincronizar", tint = Leaf)
                        }
                    },
                    colors = TopAppBarDefaults.centerAlignedTopAppBarColors(containerColor = Color.White)
                )
            },
            bottomBar = {
                NavigationBar(containerColor = Color.White, tonalElevation = 8.dp) {
                    if (!inventoryOnly) NavItem("Home", Icons.Filled.Dashboard, selectedTab == 0) { selectedTab = 0 }
                    NavItem("Stock", Icons.Filled.Inventory2, selectedTab == 1) { selectedTab = 1 }
                    if (!inventoryOnly) NavItem("Uso", Icons.Filled.LocalFireDepartment, selectedTab == 2) { selectedTab = 2 }
                    NavItem("Súper", Icons.Filled.ShoppingCart, selectedTab == 3) { selectedTab = 3 }
                    if (!inventoryOnly) NavItem("Ofertas", Icons.Filled.LocalOffer, selectedTab == 4) { selectedTab = 4 }
                }
            },
            floatingActionButton = {
                if (canEdit) when (selectedTab) {
                    0 -> ExtendedFloatingActionButton(
                        onClick = { showBotiChat = true },
                        containerColor = Leaf,
                        contentColor = Color.White
                    ) {
                        Icon(Icons.Filled.AutoAwesome, null)
                        Spacer(Modifier.width(8.dp))
                        Text("🤖 Boti Chat", fontWeight = FontWeight.Bold)
                    }
                    1 -> FloatingActionButton(onClick = { showAddDialog = true }, containerColor = Leaf, contentColor = Color.White) { Icon(Icons.Filled.Add, null) }
                    2 -> FloatingActionButton(onClick = { showOpenPicker = true }, containerColor = Gold, contentColor = Color.White) { Icon(Icons.Filled.PlayArrow, null) }
                    3 -> FloatingActionButton(onClick = { showAddShoppingDialog = true }, containerColor = Sky, contentColor = Color.White) { Icon(Icons.Filled.Add, null) }
                }
            }
        ) { padding ->
            val screenModifier = Modifier.padding(padding)
            when (if (inventoryOnly && selectedTab !in listOf(1, 3)) 1 else selectedTab) {
                0 -> HomeScreen(screenModifier, stock) { selectedTab = it }
                1 -> InventoryScreen(screenModifier, stock, onEvent = { viewModel.onEvent(it) }, onEditRequest = { if (canEdit) showEditDialog = it })
                2 -> InUseScreen(screenModifier, stock) { viewModel.onEvent(ExpensaEvent.ConsumeUnit(it)) }
                3 -> ShoppingScreen(screenModifier, shopping) { viewModel.onEvent(it) }
                4 -> OffersScreen(
                    screenModifier, 
                    savedOffers, 
                    stock, 
                    userPrefs ?: UserPrefs(),
                    expenses,
                    initialQuery = offerQuery,
                    onSetBudget = { if (canEdit) showBudgetDialog = true },
                    onAddExpense = { if (canEdit) showExpenseDialog = true },
                    onScanTicket = { if (canEdit) showScanTicketDialog = true }
                )
            }
        }
    }

    if (showBotiChat) {
        ConnectedChatDialog(onDismiss = { showBotiChat = false }, onNavigate = { tab, query ->
            selectedTab = tab
            if (query != null) offerQuery = query
            showBotiChat = false
        })
    }
    if (showScanTicketDialog) {
        ConnectedReceiptDialog(onDismiss = { showScanTicketDialog = false }, onSaved = {
            showScanTicketDialog = false
            viewModel.onEvent(ExpensaEvent.RefreshData)
            Toast.makeText(context, "Ticket registrado. Actualizando presupuesto…", Toast.LENGTH_LONG).show()
        })
    }

    // --- DIÁLOGOS ---
    if (showAddDialog) {
        AddStockDialog(
            onDismiss = { showAddDialog = false },
            onAdd = { n, b, c -> viewModel.onEvent(ExpensaEvent.AddStock(n, b, c)); showAddDialog = false }
        )
    }

    showEditDialog?.let { item ->
        EditStockDialog(
            item = item,
            onDismiss = { showEditDialog = null },
            onConfirm = { viewModel.onEvent(ExpensaEvent.UpdateStock(it)); showEditDialog = null }
        )
    }

    if (showOpenPicker) {
        OpenUnitPicker(
            stock = stock,
            onDismiss = { showOpenPicker = false },
            onSelect = { viewModel.onEvent(ExpensaEvent.OpenUnit(it)); showOpenPicker = false }
        )
    }

    if (showAddOfferDialog) {
        AddOfferDialog(
            onDismiss = { showAddOfferDialog = false },
            onAdd = { s, p, b, pr -> 
                viewModel.onEvent(ExpensaEvent.AddOffer(Offer(store = s, product = p, brand = b, price = pr, saving = "-0%")))
                showAddOfferDialog = false 
            }
        )
    }

    if (showAddShoppingDialog) {
        AddStockDialog(
            onDismiss = { showAddShoppingDialog = false },
            onAdd = { n, b, c -> viewModel.onEvent(ExpensaEvent.AddShoppingItem(n, b, c)); showAddShoppingDialog = false }
        )
    }

    if (showBudgetDialog) {
        BudgetDialog(
            currentBudget = userPrefs?.monthlyBudget ?: 0.0,
            onDismiss = { showBudgetDialog = false },
            onConfirm = { viewModel.onEvent(ExpensaEvent.SetBudget(it)); showBudgetDialog = false }
        )
    }

    if (showExpenseDialog) {
        ExpenseDialog(
            onDismiss = { showExpenseDialog = false },
            onConfirm = { amount, category ->
                viewModel.onEvent(ExpensaEvent.AddExpense(amount, category))
                showExpenseDialog = false
            }
        )
    }
}

@Composable
private fun RowScope.NavItem(label: String, icon: ImageVector, selected: Boolean, onClick: () -> Unit) {
    NavigationBarItem(
        selected = selected, 
        onClick = onClick, 
        icon = { Icon(icon, null, tint = if (selected) Leaf else Muted) }, 
        label = { Text(label, fontSize = 10.sp, fontWeight = if (selected) FontWeight.Bold else FontWeight.Normal) }
    )
}

// --- PANTALLAS ---

@Composable
private fun HomeScreen(modifier: Modifier, stock: List<StockItem>, onNavigate: (Int) -> Unit) {
    var filterMode by remember { mutableIntStateOf(0) }

    Column(modifier = Modifier.fillMaxSize().padding(horizontal = 20.dp).then(modifier)) {
        Spacer(Modifier.height(16.dp))
        Text("Tu Hogar", style = MaterialTheme.typography.headlineLarge, fontWeight = FontWeight.ExtraBold, color = Ink)
        
        LazyRow(modifier = Modifier.padding(vertical = 12.dp), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            item { FilterChip(selected = filterMode == 0, onClick = { filterMode = 0 }, label = { Text("Resumen") }, colors = FilterChipDefaults.filterChipColors(selectedContainerColor = SoftLeaf)) }
            item { FilterChip(selected = filterMode == 1, onClick = { filterMode = 1 }, label = { Text("Por Reponer") }, colors = FilterChipDefaults.filterChipColors(selectedContainerColor = SoftCoral)) }
            item { FilterChip(selected = filterMode == 2, onClick = { filterMode = 2 }, label = { Text("En Uso") }, colors = FilterChipDefaults.filterChipColors(selectedContainerColor = SoftGold)) }
        }

        LazyColumn(verticalArrangement = Arrangement.spacedBy(16.dp), modifier = Modifier.weight(1f)) {
            if (filterMode == 0) {
                item {
                    Card(colors = CardDefaults.cardColors(containerColor = Leaf), shape = RoundedCornerShape(24.dp)) {
                        Column(Modifier.padding(24.dp)) {
                            Text("Estado General", color = Color.White.copy(0.8f), fontSize = 14.sp)
                            Text("${stock.sumOf { it.stockQuantity + it.inUseCount }} Productos en Casa", color = Color.White, fontSize = 28.sp, fontWeight = FontWeight.Black)
                            Spacer(Modifier.height(12.dp))
                            LinearProgressIndicator(
                                progress = { if (stock.isEmpty()) 0f else (stock.filter { it.stockQuantity > 0 }.size.toFloat() / stock.size.toFloat()) },
                                modifier = Modifier.fillMaxWidth().height(8.dp),
                                color = Color.White,
                                trackColor = Color.White.copy(0.3f),
                                strokeCap = androidx.compose.ui.graphics.StrokeCap.Round
                            )
                        }
                    }
                }
                item { SectionTitle("Accesos Rápidos", null) {} }
                item {
                    Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                        StatCard("Nuevos", "${stock.sumOf { it.stockQuantity }}", SoftLeaf, Leaf, Icons.Filled.Inventory, Modifier.weight(1f)) { onNavigate(1) }
                        StatCard("En Uso", "${stock.sumOf { it.inUseCount }}", SoftGold, Gold, Icons.Filled.PlayCircle, Modifier.weight(1f)) { onNavigate(2) }
                    }
                }
            }

            if (filterMode == 1 || filterMode == 0) {
                val critical = stock.filter { it.stockQuantity <= 1 }
                if (critical.isNotEmpty()) {
                    item { SectionTitle("Alertas de Reposición", "Ver Lista") { filterMode = 1 } }
                    items(critical, key = { it.id }) { AlertCard(it) }
                    item {
                        TextButton(onClick = { onNavigate(3) }, modifier = Modifier.fillMaxWidth()) {
                            Text("Ir a Lista de Compras", color = Coral, fontWeight = FontWeight.Bold)
                        }
                    }
                }
            }

            if (filterMode == 2 || filterMode == 0) {
                val inUse = stock.filter { it.inUseCount > 0 }
                if (inUse.isNotEmpty()) {
                    item { SectionTitle("Abiertos actualmente", "Gestionar") { onNavigate(2) } }
                    items(inUse, key = { "home_use_${it.id}" }) { InUseDetailRow(it) }
                }
            }
            item { Spacer(Modifier.height(20.dp)) }
        }
    }
}

@Composable
private fun InventoryScreen(modifier: Modifier, stock: List<StockItem>, onEvent: (ExpensaEvent) -> Unit, onEditRequest: (StockItem) -> Unit) {
    var query by remember { mutableStateOf("") }
    val filtered = stock.filter { it.name.contains(query, true) || it.brand.contains(query, true) }

    Column(modifier = Modifier.fillMaxSize().padding(horizontal = 20.dp).then(modifier)) {
        Spacer(Modifier.height(8.dp))
        SearchBar(query) { query = it }
        
        LazyColumn(verticalArrangement = Arrangement.spacedBy(12.dp), modifier = Modifier.padding(top = 16.dp)) {
            if (stock.isEmpty()) {
                item { EmptyState("Inventario vacío.", Icons.Filled.Inbox) }
            } else {
                items(filtered, key = { it.id }) { item ->
                    InventoryCard(item, onEvent, onEditRequest)
                }
            }
            item { Spacer(Modifier.height(100.dp)) }
        }
    }
}

@Composable
private fun InUseScreen(modifier: Modifier, stock: List<StockItem>, onConsume: (StockItem) -> Unit) {
    val itemsInUse = stock.filter { it.inUseCount > 0 }
    Column(modifier = Modifier.fillMaxSize().padding(horizontal = 20.dp).then(modifier)) {
        Spacer(Modifier.height(16.dp))
        Text("En Uso", style = MaterialTheme.typography.headlineMedium, fontWeight = FontWeight.Black, color = Ink)
        
        LazyColumn(verticalArrangement = Arrangement.spacedBy(12.dp), modifier = Modifier.padding(top = 16.dp)) {
            if (itemsInUse.isEmpty()) {
                item { EmptyState("Nada abierto.", Icons.Filled.PlayCircle) }
            } else {
                items(itemsInUse, key = { it.id }) { item ->
                    Card(colors = CardDefaults.cardColors(containerColor = SoftGold), shape = RoundedCornerShape(16.dp)) {
                        Row(Modifier.padding(16.dp), verticalAlignment = Alignment.CenterVertically) {
                            Column(Modifier.weight(1f)) {
                                Text(item.name, fontWeight = FontWeight.Bold, fontSize = 18.sp)
                                Text("${item.brand} • ${item.inUseCount} abierta(s)", color = Ink.copy(0.7f), fontSize = 12.sp)
                            }
                            Button(onClick = { onConsume(item) }, colors = ButtonDefaults.buttonColors(containerColor = Coral)) {
                                Text("Terminar")
                            }
                        }
                    }
                }
            }
            item { Spacer(Modifier.height(100.dp)) }
        }
    }
}

@Composable
private fun ShoppingScreen(modifier: Modifier, shopping: List<ShoppingItem>, onEvent: (ExpensaEvent) -> Unit) {
    val grouped = shopping.groupBy { it.category }
    Column(modifier = Modifier.fillMaxSize().then(modifier)) {
        Spacer(Modifier.height(16.dp))
        Text("Lista de Compras", style = MaterialTheme.typography.headlineMedium, fontWeight = FontWeight.Black, color = Ink, modifier = Modifier.padding(horizontal = 16.dp))
        
        LazyColumn(verticalArrangement = Arrangement.spacedBy(12.dp), modifier = Modifier.padding(top = 16.dp)) {
            if (shopping.isEmpty()) {
                item { EmptyState("Lista vacía.", Icons.Filled.ShoppingCartCheckout) }
            } else {
                grouped.forEach { (cat, items) ->
                    item { Text(cat.uppercase(), fontWeight = FontWeight.Black, color = Sky, fontSize = 12.sp, modifier = Modifier.padding(top = 8.dp, start = 20.dp)) }
                    items(items, key = { it.id }) { item ->
                        ShoppingRow(
                            item = item,
                            onToggle = { onEvent(ExpensaEvent.ToggleShopping(it)) },
                            onUpdateQuantity = { id, qty -> onEvent(ExpensaEvent.UpdateShoppingQuantity(id, qty)) },
                            onDelete = { onEvent(ExpensaEvent.DeleteShoppingItem(it)) },
                            onMove = { onEvent(ExpensaEvent.MoveToStock(it)) }
                        )
                    }
                }
            }
            item { Spacer(Modifier.height(100.dp)) }
        }
    }
}

@Composable
private fun OffersScreen(
    modifier: Modifier, 
    userOffers: List<Offer>, 
    stock: List<StockItem>,
    userPrefs: UserPrefs,
    expenses: List<Expense>,
    initialQuery: String,
    onSetBudget: () -> Unit,
    onAddExpense: () -> Unit,
    onScanTicket: () -> Unit
) {
    val uriHandler = LocalUriHandler.current
    val critical = stock.filter { it.stockQuantity <= 1 }

    Column(modifier = Modifier.fillMaxSize().then(modifier)) {
        LazyColumn(modifier = Modifier.weight(1f).padding(horizontal = 16.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
            item { 
                Spacer(Modifier.height(16.dp))
                Text("Súper Online", style = MaterialTheme.typography.headlineSmall, fontWeight = FontWeight.Black)
            }

            item {
                Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    StoreButton("Coto", "https://www.cotodigital3.com.ar/", Coral, Modifier.weight(1f))
                    StoreButton("Carrefour", "https://www.carrefour.com.ar/", Sky, Modifier.weight(1f))
                    StoreButton("Día", "https://www.diaonline.com.ar/", Gold, Modifier.weight(1f))
                }
            }

            item { ConnectedOfferSearch(initialQuery) }

            if (expenses.isNotEmpty()) {
                item { SectionTitle("Reporte de Gastos", null) {} }
                item {
                    val groupedExpenses = expenses.groupBy { it.category }
                    Card(
                        colors = CardDefaults.cardColors(containerColor = Color.White),
                        shape = RoundedCornerShape(16.dp),
                        elevation = CardDefaults.cardElevation(1.dp)
                    ) {
                        Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                            groupedExpenses.forEach { (cat, list) ->
                                val total = list.sumOf { it.amount }
                                Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                                    Text(cat, fontSize = 14.sp, color = Muted, fontWeight = FontWeight.Medium)
                                    Text("$ ${String.format("%.2f", total)}", fontSize = 14.sp, fontWeight = FontWeight.ExtraBold, color = Leaf)
                                }
                            }
                            HorizontalDivider(color = Canvas)
                            Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                                Text("TOTAL ACUMULADO", fontSize = 12.sp, fontWeight = FontWeight.Bold, color = Ink)
                                Text("$ ${String.format("%.2f", expenses.sumOf { it.amount })}", fontSize = 14.sp, fontWeight = FontWeight.Black, color = Ink)
                            }
                        }
                    }
                }
            }

            if (critical.isNotEmpty()) {
                item { SectionTitle("Faltantes", null) {} }
                items(critical) { item ->
                    Card(
                        onClick = { uriHandler.openUri("https://ratoneando.ar/?q=${java.net.URLEncoder.encode(item.name, "UTF-8")}") },
                        modifier = Modifier.fillMaxWidth(),
                        colors = CardDefaults.cardColors(containerColor = Color.White),
                        shape = RoundedCornerShape(12.dp)
                    ) {
                        Row(Modifier.padding(12.dp), verticalAlignment = Alignment.CenterVertically) {
                            Icon(Icons.Filled.Search, null, tint = Lavender, modifier = Modifier.size(18.dp))
                            Spacer(Modifier.width(8.dp))
                            Text(item.name, fontSize = 14.sp, fontWeight = FontWeight.Bold, modifier = Modifier.weight(1f))
                            Text("Comparar", color = Leaf, fontSize = 12.sp, fontWeight = FontWeight.Bold)
                        }
                    }
                }
            }
            item { Spacer(Modifier.height(20.dp)) }
        }

        Card(
            modifier = Modifier.fillMaxWidth().padding(12.dp),
            colors = CardDefaults.cardColors(containerColor = Ink),
            shape = RoundedCornerShape(20.dp)
        ) {
            Column(Modifier.padding(16.dp)) {
                Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween, verticalAlignment = Alignment.CenterVertically) {
                    Column {
                        Text("Presupuesto", color = Color.White.copy(0.7f), fontSize = 12.sp)
                        Text("$ ${String.format("%.2f", userPrefs.monthlyBudget)}", color = Color.White, fontSize = 18.sp, fontWeight = FontWeight.Bold)
                    }
                    IconButton(onClick = onSetBudget, modifier = Modifier.size(32.dp)) { Icon(Icons.Filled.Settings, null, tint = Color.White, modifier = Modifier.size(20.dp)) }
                }
                val remaining = userPrefs.monthlyBudget - userPrefs.totalSpent
                val progress = if (userPrefs.monthlyBudget > 0) (userPrefs.totalSpent / userPrefs.monthlyBudget).toFloat() else 0f
                LinearProgressIndicator(progress = { progress.coerceIn(0f, 1f) }, modifier = Modifier.fillMaxWidth().height(6.dp).padding(vertical = 8.dp), color = if (remaining < 0) Coral else Leaf, trackColor = Color.White.copy(0.1f), strokeCap = androidx.compose.ui.graphics.StrokeCap.Round)
                Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween, verticalAlignment = Alignment.CenterVertically) {
                    Column {
                        Text("Quedan", color = Color.White.copy(0.7f), fontSize = 11.sp)
                        Text("$ ${String.format("%.2f", remaining)}", color = if (remaining < 0) Coral else Color.White, fontSize = 16.sp, fontWeight = FontWeight.ExtraBold)
                    }
                    Row(horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                        Button(onClick = onScanTicket, colors = ButtonDefaults.buttonColors(containerColor = Leaf), shape = RoundedCornerShape(10.dp), modifier = Modifier.height(36.dp), contentPadding = PaddingValues(horizontal = 8.dp)) { Text("ESCANEAR TICKET", fontSize = 10.sp, fontWeight = FontWeight.Bold) }
                        Button(onClick = onAddExpense, colors = ButtonDefaults.buttonColors(containerColor = Lavender), shape = RoundedCornerShape(10.dp), modifier = Modifier.height(36.dp), contentPadding = PaddingValues(horizontal = 8.dp)) { Text("CARGAR TICKET", fontSize = 10.sp, fontWeight = FontWeight.Bold) }
                    }
                }
            }
        }
    }
}

// --- COMPONENTES UI ---

@Composable
private fun InventoryCard(item: StockItem, onEvent: (ExpensaEvent) -> Unit, onEdit: (StockItem) -> Unit) {
    val critical = item.stockQuantity <= 1
    Card(colors = CardDefaults.cardColors(containerColor = Color.White), shape = RoundedCornerShape(16.dp), elevation = CardDefaults.cardElevation(2.dp), modifier = Modifier.fillMaxWidth().padding(horizontal = 4.dp)) {
        Column(Modifier.padding(12.dp)) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                ProductSymbolicIcon(name = item.name, category = item.category, modifier = Modifier.size(42.dp), backgroundColor = if (critical) SoftCoral else SoftLeaf, iconTint = if (critical) Coral else Leaf)
                Spacer(Modifier.width(12.dp))
                Column(Modifier.weight(1f)) {
                    Text(item.name, fontWeight = FontWeight.Bold, fontSize = 16.sp, color = Ink, maxLines = 1, overflow = TextOverflow.Ellipsis)
                    Text("${item.brand} • ${item.category}", color = Muted, fontSize = 11.sp)
                }
                IconButton(onClick = { onEdit(item) }, modifier = Modifier.size(32.dp)) { Icon(Icons.Filled.Edit, null, tint = Muted, modifier = Modifier.size(18.dp)) }
                IconButton(onClick = { onEvent(ExpensaEvent.DeleteStock(item)) }, modifier = Modifier.size(32.dp)) { Icon(Icons.Filled.Delete, null, tint = Coral, modifier = Modifier.size(18.dp)) }
            }
            Spacer(Modifier.height(8.dp)); HorizontalDivider(color = Canvas, thickness = 1.dp); Spacer(Modifier.height(8.dp))
            Row(Modifier.fillMaxWidth(), verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.SpaceBetween) {
                Column(horizontalAlignment = Alignment.CenterHorizontally) {
                    Text("STOCK", fontSize = 9.sp, fontWeight = FontWeight.Bold, color = if (critical) Coral else Leaf)
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        IconButton(onClick = { onEvent(ExpensaEvent.UpdateStock(item.copy(stockQuantity = (item.stockQuantity - 1).coerceAtLeast(0)))) }, modifier = Modifier.size(24.dp)) { Icon(Icons.Filled.RemoveCircleOutline, null, tint = Muted, modifier = Modifier.size(16.dp)) }
                        Text("${item.stockQuantity}", fontWeight = FontWeight.Black, fontSize = 16.sp, modifier = Modifier.padding(horizontal = 4.dp))
                        IconButton(onClick = { onEvent(ExpensaEvent.UpdateStock(item.copy(stockQuantity = item.stockQuantity + 1))) }, modifier = Modifier.size(24.dp)) { Icon(Icons.Filled.AddCircleOutline, null, tint = Leaf, modifier = Modifier.size(16.dp)) }
                    }
                }
                Column(horizontalAlignment = Alignment.CenterHorizontally) {
                    Text("USO", fontSize = 9.sp, fontWeight = FontWeight.Bold, color = Gold)
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        IconButton(onClick = { onEvent(ExpensaEvent.UpdateStock(item.copy(inUseCount = (item.inUseCount - 1).coerceAtLeast(0)))) }, modifier = Modifier.size(24.dp)) { Icon(Icons.Filled.RemoveCircleOutline, null, tint = Muted, modifier = Modifier.size(16.dp)) }
                        Text("${item.inUseCount}", fontWeight = FontWeight.Black, fontSize = 16.sp, modifier = Modifier.padding(horizontal = 4.dp))
                        IconButton(onClick = { onEvent(ExpensaEvent.UpdateStock(item.copy(inUseCount = item.inUseCount + 1))) }, modifier = Modifier.size(24.dp)) { Icon(Icons.Filled.AddCircleOutline, null, tint = Gold, modifier = Modifier.size(16.dp)) }
                    }
                }
                Column(horizontalAlignment = Alignment.CenterHorizontally, modifier = Modifier.padding(start = 4.dp)) {
                    Text("TOTAL", fontSize = 9.sp, fontWeight = FontWeight.Bold, color = Ink)
                    Text("${item.stockQuantity + item.inUseCount}", fontWeight = FontWeight.ExtraBold, fontSize = 18.sp, color = Ink)
                }
            }
        }
    }
}

@Composable
private fun ShoppingRow(item: ShoppingItem, onToggle: (String) -> Unit, onUpdateQuantity: (String, Int) -> Unit, onDelete: (String) -> Unit, onMove: (ShoppingItem) -> Unit) {
    Card(colors = CardDefaults.cardColors(containerColor = Color.White), shape = RoundedCornerShape(12.dp), elevation = CardDefaults.cardElevation(2.dp), modifier = Modifier.fillMaxWidth().padding(horizontal = 16.dp)) {
        Column(Modifier.padding(10.dp)) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Checkbox(checked = item.checked, onCheckedChange = { onToggle(item.id) }, colors = CheckboxDefaults.colors(checkedColor = Leaf), modifier = Modifier.size(32.dp))
                ProductSymbolicIcon(name = item.name, category = item.category, modifier = Modifier.size(36.dp), backgroundColor = SoftSky, iconTint = Sky)
                Spacer(Modifier.width(10.dp))
                Column(Modifier.weight(1f)) {
                    Text(item.name, fontWeight = FontWeight.Bold, color = if (item.checked) Muted else Ink, fontSize = 15.sp, maxLines = 1, overflow = TextOverflow.Ellipsis)
                    if (item.suggestedStore != null) Text("📍 ${item.suggestedStore}", color = Leaf, fontSize = 10.sp, fontWeight = FontWeight.Bold)
                }
                IconButton(onClick = { onDelete(item.id) }, modifier = Modifier.size(28.dp)) { Icon(Icons.Filled.Delete, null, tint = Coral.copy(0.5f), modifier = Modifier.size(18.dp)) }
            }
            Row(Modifier.fillMaxWidth().padding(top = 8.dp), horizontalArrangement = Arrangement.SpaceBetween, verticalAlignment = Alignment.CenterVertically) {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    IconButton(onClick = { if (item.quantity > 1) onUpdateQuantity(item.id, item.quantity - 1) }, modifier = Modifier.size(28.dp)) { Icon(Icons.Filled.RemoveCircleOutline, null, tint = Muted, modifier = Modifier.size(20.dp)) }
                    Text("${item.quantity}", fontWeight = FontWeight.Black, fontSize = 15.sp, modifier = Modifier.padding(horizontal = 4.dp))
                    IconButton(onClick = { onUpdateQuantity(item.id, item.quantity + 1) }, modifier = Modifier.size(28.dp)) { Icon(Icons.Filled.AddCircleOutline, null, tint = Leaf, modifier = Modifier.size(20.dp)) }
                }
                Button(onClick = { onMove(item) }, colors = ButtonDefaults.buttonColors(containerColor = Leaf), shape = RoundedCornerShape(8.dp), modifier = Modifier.height(30.dp), contentPadding = PaddingValues(horizontal = 10.dp)) { Text("A STOCK", fontSize = 10.sp, fontWeight = FontWeight.Black) }
            }
        }
    }
}

@Composable
private fun BudgetDialog(currentBudget: Double, onDismiss: () -> Unit, onConfirm: (Double) -> Unit) {
    var budget by remember { mutableStateOf(if (currentBudget > 0) currentBudget.toString() else "") }
    AlertDialog(onDismissRequest = onDismiss, title = { Text("Presupuesto Mensual", fontWeight = FontWeight.Bold) },
        text = { OutlinedTextField(value = budget, onValueChange = { budget = it }, label = { Text("Monto disponible") }, singleLine = true, textStyle = androidx.compose.ui.text.TextStyle(color = Color.Black, fontSize = 15.sp, fontWeight = FontWeight.Bold), colors = OutlinedTextFieldDefaults.colors(focusedTextColor = Color.Black, unfocusedTextColor = Color.Black), keyboardOptions = androidx.compose.foundation.text.KeyboardOptions(keyboardType = androidx.compose.ui.text.input.KeyboardType.Number)) },
        confirmButton = { Button(onClick = { onConfirm(budget.toDoubleOrNull() ?: 0.0) }, colors = ButtonDefaults.buttonColors(containerColor = Leaf)) { Text("DEFINIR") } },
        dismissButton = { TextButton(onClick = onDismiss) { Text("CANCELAR") } }
    )
}

@Composable
private fun ExpenseDialog(onDismiss: () -> Unit, onConfirm: (Double, String) -> Unit) {
    var amount by remember { mutableStateOf("") }; var category by remember { mutableStateOf(categories[0]) }
    AlertDialog(onDismissRequest = onDismiss, title = { Text("Registrar Gasto", fontWeight = FontWeight.Bold) },
        text = { Column(verticalArrangement = Arrangement.spacedBy(12.dp)) {
            OutlinedTextField(value = amount, onValueChange = { amount = it }, label = { Text("Monto del ticket") }, singleLine = true, textStyle = androidx.compose.ui.text.TextStyle(color = Color.Black, fontSize = 15.sp, fontWeight = FontWeight.Bold), colors = OutlinedTextFieldDefaults.colors(focusedTextColor = Color.Black, unfocusedTextColor = Color.Black), keyboardOptions = androidx.compose.foundation.text.KeyboardOptions(keyboardType = androidx.compose.ui.text.input.KeyboardType.Number))
            Text("Categoría:", fontSize = 12.sp, fontWeight = FontWeight.Bold)
            Row(Modifier.fillMaxWidth().horizontalScroll(rememberScrollState()), horizontalArrangement = Arrangement.spacedBy(4.dp)) {
                categories.forEach { cat -> FilterChip(selected = category == cat, onClick = { category = cat }, label = { Text(cat, fontSize = 10.sp) }) }
            }
        }},
        confirmButton = { Button(onClick = { onConfirm(amount.toDoubleOrNull() ?: 0.0, category) }, colors = ButtonDefaults.buttonColors(containerColor = Coral)) { Text("RESTAR") } },
        dismissButton = { TextButton(onClick = onDismiss) { Text("CANCELAR") } }
    )
}

@Composable
private fun StoreButton(name: String, url: String, color: Color, modifier: Modifier) {
    val uriHandler = LocalUriHandler.current
    Button(onClick = { uriHandler.openUri(url) }, modifier = modifier.height(40.dp), colors = ButtonDefaults.buttonColors(containerColor = color), shape = RoundedCornerShape(10.dp), contentPadding = PaddingValues(0.dp)) { Text(name, fontWeight = FontWeight.Bold, fontSize = 11.sp) }
}

@Composable
private fun StatCard(title: String, value: String, bg: Color, tint: Color, icon: ImageVector, modifier: Modifier, onClick: () -> Unit) {
    Card(modifier = modifier, colors = CardDefaults.cardColors(containerColor = bg), shape = RoundedCornerShape(20.dp), onClick = onClick) {
        Column(Modifier.padding(16.dp)) { Icon(icon, null, tint = tint); Text(value, fontSize = 22.sp, fontWeight = FontWeight.Black, color = Ink); Text(title, fontSize = 12.sp, color = Ink.copy(0.6f)) }
    }
}

@Composable
private fun AlertCard(item: StockItem) {
    Card(colors = CardDefaults.cardColors(containerColor = SoftCoral.copy(0.4f)), shape = RoundedCornerShape(16.dp), border = androidx.compose.foundation.BorderStroke(1.dp, Coral)) {
        Row(Modifier.padding(12.dp), verticalAlignment = Alignment.CenterVertically) {
            ProductSymbolicIcon(name = item.name, category = item.category, backgroundColor = SoftCoral, iconTint = Coral)
            Spacer(Modifier.width(12.dp))
            Column { Text(item.name, fontWeight = FontWeight.Bold, color = Ink); Text("Solo queda ${item.stockQuantity} unidad cerrada.", fontSize = 12.sp, color = Muted) }
        }
    }
}

@Composable
private fun InUseDetailRow(item: StockItem) {
    Row(verticalAlignment = Alignment.CenterVertically, modifier = Modifier.padding(vertical = 4.dp)) {
        ProductSymbolicIcon(name = item.name, category = item.category, modifier = Modifier.size(32.dp), backgroundColor = SoftGold, iconTint = Gold)
        Spacer(Modifier.width(12.dp))
        Text(item.name, modifier = Modifier.weight(1f), fontWeight = FontWeight.Medium); Text("${item.inUseCount} abierto(s)", color = Muted, fontSize = 12.sp)
    }
}

@Composable
private fun EmptyState(text: String, icon: ImageVector) {
    Column(Modifier.fillMaxWidth().padding(40.dp), horizontalAlignment = Alignment.CenterHorizontally) { Icon(icon, null, modifier = Modifier.size(64.dp), tint = Color.LightGray); Spacer(Modifier.height(16.dp)); Text(text, color = Muted, fontSize = 14.sp) }
}

@Composable
private fun SectionTitle(title: String, action: String?, onActionClick: () -> Unit) {
    Row(Modifier.fillMaxWidth().padding(top = 8.dp), verticalAlignment = Alignment.CenterVertically) {
        Text(title, fontWeight = FontWeight.Black, color = Ink, fontSize = 18.sp); Spacer(Modifier.weight(1f))
        if (action != null) { TextButton(onClick = onActionClick) { Text(action, color = Leaf, fontSize = 13.sp, fontWeight = FontWeight.Bold) } }
    }
}

private fun getSymbolicIconForProduct(name: String, category: String): ImageVector {
    val q = name.lowercase()
    return when {
        q.contains("leche") || q.contains("yogur") || q.contains("crema") || q.contains("sachet") -> Icons.Filled.LocalDrink
        q.contains("café") || q.contains("cafe") || q.contains("té") || q.contains("mate") || q.contains("yerba") -> Icons.Filled.Coffee
        q.contains("arroz") || q.contains("fideos") || q.contains("pasta") || q.contains("harina") -> Icons.Filled.BakeryDining
        q.contains("pan") || q.contains("galleta") || q.contains("factura") || q.contains("medialuna") -> Icons.Filled.BakeryDining
        q.contains("pollo") || q.contains("carne") || q.contains("asado") || q.contains("milanesa") || q.contains("pescado") -> Icons.Filled.Restaurant
        q.contains("tomate") || q.contains("papa") || q.contains("cebolla") || q.contains("fruta") || q.contains("manzana") -> Icons.Filled.Eco
        q.contains("detergente") || q.contains("jabón") || q.contains("jabon") || q.contains("lavandina") || q.contains("limpieza") -> Icons.Filled.CleanHands
        q.contains("papel") || q.contains("higiénico") || q.contains("rollos") -> Icons.Filled.Home
        category == "Carnicería" -> Icons.Filled.Restaurant
        category == "Verdulería" -> Icons.Filled.Eco
        category == "Limpieza" -> Icons.Filled.CleanHands
        category == "Hogar" -> Icons.Filled.Home
        else -> Icons.Filled.ShoppingBasket
    }
}

@Composable
private fun ProductSymbolicIcon(
    name: String,
    category: String,
    modifier: Modifier = Modifier.size(36.dp),
    backgroundColor: Color = SoftLeaf,
    iconTint: Color = Leaf
) {
    val icon = getSymbolicIconForProduct(name, category)
    Box(
        modifier = modifier.background(backgroundColor, RoundedCornerShape(10.dp)),
        contentAlignment = Alignment.Center
    ) {
        Icon(
            imageVector = icon,
            contentDescription = name,
            tint = iconTint,
            modifier = Modifier.size(20.dp)
        )
    }
}

@Composable
private fun SearchBar(query: String, onQueryChange: (String) -> Unit) {
    VoiceOutlinedTextField(
        value = query,
        onValueChange = onQueryChange,
        modifier = Modifier.fillMaxWidth(),
        placeholder = { Text("Buscar...") },
        leadingIcon = { Icon(Icons.Filled.Search, null) },
        shape = RoundedCornerShape(12.dp),
        singleLine = true
    )
}

@Composable
private fun AddStockDialog(onDismiss: () -> Unit, onAdd: (String, String, String) -> Unit) {
    var n by remember { mutableStateOf("") }
    var b by remember { mutableStateOf("") }
    var c by remember { mutableStateOf("Comestibles") }

    val context = LocalContext.current
    val fullProductLauncher = rememberLauncherForActivityResult(ActivityResultContracts.StartActivityForResult()) { result ->
        if (result.resultCode == Activity.RESULT_OK) {
            val spokenText = result.data?.getStringArrayListExtra(RecognizerIntent.EXTRA_RESULTS)?.firstOrNull()
            if (!spokenText.isNullOrBlank()) {
                val parts = spokenText.trim().split("\\s+".toRegex())
                if (parts.size >= 2) {
                    b = parts.last()
                    n = parts.dropLast(1).joinToString(" ")
                } else {
                    n = spokenText.trim()
                }
            }
        }
    }

    AlertDialog(onDismissRequest = onDismiss, title = { Text("Cargar Producto", fontWeight = FontWeight.Black) },
        text = { Column(verticalArrangement = Arrangement.spacedBy(12.dp)) {
            Button(
                onClick = {
                    val intent = Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH).apply {
                        putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL, RecognizerIntent.LANGUAGE_MODEL_FREE_FORM)
                        putExtra(RecognizerIntent.EXTRA_LANGUAGE, "es-AR")
                        putExtra(RecognizerIntent.EXTRA_PROMPT, "Dictá el producto (ej: Arroz Lucchetti)...")
                    }
                    try {
                        fullProductLauncher.launch(intent)
                    } catch (e: Exception) {
                        Toast.makeText(context, "Reconocimiento de voz no disponible", Toast.LENGTH_SHORT).show()
                    }
                },
                colors = ButtonDefaults.buttonColors(containerColor = SoftLeaf),
                shape = RoundedCornerShape(10.dp),
                modifier = Modifier.fillMaxWidth()
            ) {
                Icon(Icons.Filled.Mic, contentDescription = null, tint = Leaf)
                Spacer(Modifier.width(8.dp))
                Text("Dictar producto completo por voz", color = Ink, fontWeight = FontWeight.Bold, fontSize = 12.sp)
            }

            VoiceOutlinedTextField(value = n, onValueChange = { n = it }, label = { Text("Nombre") }, singleLine = true)
            VoiceOutlinedTextField(value = b, onValueChange = { b = it }, label = { Text("Marca") }, singleLine = true)
            Text("Categoría", fontWeight = FontWeight.Bold, fontSize = 12.sp)
            Row(Modifier.fillMaxWidth().horizontalScroll(rememberScrollState()), horizontalArrangement = Arrangement.spacedBy(4.dp)) {
                categories.forEach { cat -> FilterChip(selected = c == cat, onClick = { c = cat }, label = { Text(cat, fontSize = 10.sp) }) }
            }
        }},
        confirmButton = { Button(enabled = n.isNotBlank(), onClick = { onAdd(n, b, c) }, colors = ButtonDefaults.buttonColors(containerColor = Leaf)) { Text("GUARDAR") } },
        dismissButton = { TextButton(onClick = onDismiss) { Text("CANCELAR") } }
    )
}

@Composable
private fun EditStockDialog(item: StockItem, onDismiss: () -> Unit, onConfirm: (StockItem) -> Unit) {
    var n by remember { mutableStateOf(item.name) }; var b by remember { mutableStateOf(item.brand) }; var c by remember { mutableStateOf(item.category) }
    AlertDialog(onDismissRequest = onDismiss, title = { Text("Editar Producto", fontWeight = FontWeight.Black) },
        text = { Column(verticalArrangement = Arrangement.spacedBy(12.dp)) {
            VoiceOutlinedTextField(value = n, onValueChange = { n = it }, label = { Text("Nombre") }, singleLine = true)
            VoiceOutlinedTextField(value = b, onValueChange = { b = it }, label = { Text("Marca") }, singleLine = true)
            Text("Categoría", fontWeight = FontWeight.Bold, fontSize = 12.sp)
            Row(Modifier.fillMaxWidth().horizontalScroll(rememberScrollState()), horizontalArrangement = Arrangement.spacedBy(4.dp)) {
                categories.forEach { cat -> FilterChip(selected = c == cat, onClick = { c = cat }, label = { Text(cat, fontSize = 10.sp) }) }
            }
        }},
        confirmButton = { Button(enabled = n.isNotBlank(), onClick = { onConfirm(item.copy(name = n, brand = b, category = c)) }, colors = ButtonDefaults.buttonColors(containerColor = Leaf)) { Text("GUARDAR") } },
        dismissButton = { TextButton(onClick = onDismiss) { Text("CANCELAR") } }
    )
}

@Composable
private fun AddOfferDialog(onDismiss: () -> Unit, onAdd: (String, String, String, String) -> Unit) {
    var s by remember { mutableStateOf("") }; var p by remember { mutableStateOf("") }; var b by remember { mutableStateOf("") }; var pr by remember { mutableStateOf("") }
    AlertDialog(onDismissRequest = onDismiss, title = { Text("Nueva Oferta Manual", fontWeight = FontWeight.Black) },
        text = { Column(verticalArrangement = Arrangement.spacedBy(12.dp)) {
            VoiceOutlinedTextField(value = s, onValueChange = { s = it }, label = { Text("Tienda") }, singleLine = true)
            VoiceOutlinedTextField(value = p, onValueChange = { p = it }, label = { Text("Producto") }, singleLine = true)
            VoiceOutlinedTextField(value = b, onValueChange = { b = it }, label = { Text("Marca") }, singleLine = true)
            VoiceOutlinedTextField(value = pr, onValueChange = { pr = it }, label = { Text("Precio") }, singleLine = true)
        }},
        confirmButton = { Button(enabled = s.isNotBlank() && p.isNotBlank(), onClick = { onAdd(s, p, b, pr) }, colors = ButtonDefaults.buttonColors(containerColor = Lavender)) { Text("GUARDAR") } },
        dismissButton = { TextButton(onClick = onDismiss) { Text("CANCELAR") } }
    )
}

@Composable
private fun OpenUnitPicker(stock: List<StockItem>, onDismiss: () -> Unit, onSelect: (StockItem) -> Unit) {
    val available = stock.filter { it.stockQuantity > 0 }
    AlertDialog(onDismissRequest = onDismiss, title = { Text("¿Qué vas a abrir?", fontWeight = FontWeight.Black) },
        text = { LazyColumn(Modifier.height(250.dp)) {
            if (available.isEmpty()) item { Text("No hay nada cerrado para abrir.", color = Muted) }
            else items(available) { item -> TextButton(onClick = { onSelect(item) }, modifier = Modifier.fillMaxWidth()) { Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) { Text("${item.name} (${item.brand})", color = Ink, fontWeight = FontWeight.Bold); Text("${item.stockQuantity} disp.", color = Leaf, fontSize = 12.sp) } } }
        }},
        confirmButton = { TextButton(onClick = onDismiss) { Text("CERRAR") } }
    )
}
